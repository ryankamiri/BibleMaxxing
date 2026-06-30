import Foundation

enum PublicPage: String, CaseIterable, Identifiable {
    case privacy
    case terms
    case community
    case support

    var id: String { rawValue }

    var title: String {
        switch self {
        case .privacy:
            return "Privacy"
        case .terms:
            return "Terms"
        case .community:
            return "Guidelines"
        case .support:
            return "Support"
        }
    }
}

enum APIClientError: LocalizedError {
    case invalidURL
    case invalidResponse
    case server(statusCode: Int, message: String)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "We couldn't prepare that request. Please try again."
        case .invalidResponse:
            return "We couldn't read the server response. Please try again."
        case let .server(statusCode, message):
            if statusCode >= 500 {
                return "BibleMaxxing is having trouble right now. Please try again."
            }
            return message.isEmpty ? "We couldn't complete that request. Please try again." : message
        }
    }
}

final class APIClient {
    static let production = APIClient(
        baseURL: URL(string: "https://api.tailortom.org/biblemaxxing/api/v1")!
    )

    let baseURL: URL
    var bearerToken: String?

    private let session: URLSession
    private let encoder: JSONEncoder
    private let decoder: JSONDecoder

    init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session

        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        self.encoder = encoder

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .iso8601
        self.decoder = decoder
    }

    func login(email: String, password: String) async throws -> AuthResponse {
        try await request("/auth/login", method: "POST", body: LoginRequest(email: email, password: password))
    }

    func register(username: String, email: String, password: String, birthday: String?) async throws -> AuthResponse {
        try await request(
            "/auth/register",
            method: "POST",
            body: RegisterRequest(username: username, email: email, password: password, birthday: birthday)
        )
    }

    func signInWithApple(identityToken: String?, authorizationCode: String?) async throws -> AuthResponse {
        try await request(
            "/auth/apple",
            method: "POST",
            body: AppleAuthRequest(identityToken: identityToken, authorizationCode: authorizationCode)
        )
    }

    func currentUser() async throws -> User {
        try await request("/me", method: "GET")
    }

    func submitOnboarding(topics: [String], intensity: String) async throws -> User {
        try await request(
            "/onboarding",
            method: "POST",
            body: OnboardingRequest(topics: topics, intensity: intensity)
        )
    }

    func fetchFeed(limit: Int = 12, excludingVideoIDs: [String] = []) async throws -> FeedResponse {
        var query = [URLQueryItem(name: "limit", value: String(limit))]
        query.append(contentsOf: excludingVideoIDs.map { videoID in
            URLQueryItem(name: "exclude_video_ids", value: videoID)
        })
        return try await request("/feed", method: "GET", query: query)
    }

    func youtubePlayerPageURL(videoID: String, autoplay: Bool = false) -> URL {
        let serviceRoot = serviceRootURL()
        let playerURL = serviceRoot
            .appendingPathComponent("player")
            .appendingPathComponent(videoID)
        var components = URLComponents(url: playerURL, resolvingAgainstBaseURL: false)
        components?.queryItems = [
            URLQueryItem(name: "autoplay", value: autoplay ? "1" : "0")
        ]
        return components?.url ?? playerURL
    }

    func publicPageURL(_ page: PublicPage) -> URL {
        serviceRootURL().appendingPathComponent(page.rawValue)
    }

    private func serviceRootURL() -> URL {
        var serviceRoot = baseURL
        if serviceRoot.lastPathComponent == "v1" {
            serviceRoot.deleteLastPathComponent()
        }
        if serviceRoot.lastPathComponent == "api" {
            serviceRoot.deleteLastPathComponent()
        }
        return serviceRoot
    }

    func recordFeedImpression(videoID: String, position: Int) async throws {
        try await requestEmpty(
            "/feed/impressions",
            method: "POST",
            body: FeedImpressionRequest(videoID: videoID, position: position)
        )
    }

    func recordWatch(videoID: String, secondsWatched: Double, percentComplete: Double, rewatched: Bool, eventType: VideoWatchEventKind) async throws {
        try await requestEmpty(
            "/videos/\(videoID.urlPathEscaped)/watch",
            method: "POST",
            body: VideoWatchRequest(
                secondsWatched: secondsWatched,
                percentComplete: percentComplete,
                rewatched: rewatched,
                eventType: eventType
            )
        )
    }

    func setLike(videoID: String, liked: Bool) async throws {
        let path = "/videos/\(videoID.urlPathEscaped)/like"
        if liked {
            try await requestEmpty(path, method: "POST")
        } else {
            try await requestEmpty(path, method: "DELETE")
        }
    }

    func setSave(videoID: String, saved: Bool) async throws {
        let path = "/videos/\(videoID.urlPathEscaped)/save"
        if saved {
            try await requestEmpty(path, method: "POST")
        } else {
            try await requestEmpty(path, method: "DELETE")
        }
    }

    func markNotInterested(videoID: String, reason: String? = nil) async throws {
        try await requestEmpty(
            "/videos/\(videoID.urlPathEscaped)/not-interested",
            method: "POST",
            body: NotInterestedRequest(reason: reason)
        )
    }

    func followCreator(creatorID: String) async throws {
        try await requestEmpty(
            "/creators/\(creatorID.urlPathEscaped)/follow",
            method: "POST",
            body: FollowRequest(source: "feed")
        )
    }

    func followTopic(slug: String) async throws {
        try await requestEmpty("/topics/\(slug.urlPathEscaped)/follow", method: "POST", body: FollowRequest(source: "feed"))
    }

    func blockCreator(creatorID: String) async throws {
        try await requestEmpty("/creators/\(creatorID.urlPathEscaped)/block", method: "POST")
    }

    func comments(videoID: String) async throws -> [Comment] {
        try await request("/videos/\(videoID.urlPathEscaped)/comments", method: "GET")
    }

    func addComment(videoID: String, body: String) async throws -> Comment {
        try await request(
            "/videos/\(videoID.urlPathEscaped)/comments",
            method: "POST",
            body: CreateCommentRequest(body: body)
        )
    }

    func reportVideo(videoID: String, reason: String, notes: String?) async throws {
        try await requestEmpty(
            "/videos/\(videoID.urlPathEscaped)/report",
            method: "POST",
            body: ReportRequest(reason: reason, details: notes)
        )
    }

    func reportComment(commentID: String, reason: String, notes: String?) async throws {
        try await requestEmpty(
            "/comments/\(commentID.urlPathEscaped)/report",
            method: "POST",
            body: ReportRequest(reason: reason, details: notes)
        )
    }

    func deleteAccount() async throws {
        try await requestEmpty("/me", method: "DELETE")
    }

    func search(query: String) async throws -> SearchResponse {
        try await request("/search", method: "GET", query: [URLQueryItem(name: "q", value: query)])
    }

    func adminRecommendationEval(limit: Int = 30) async throws -> AdminEvalScorecard {
        try await request(
            "/admin/evals/recommendations",
            method: "GET",
            query: [URLQueryItem(name: "limit", value: String(limit))]
        )
    }

    func adminRedTeamIngestEval() async throws -> AdminEvalScorecard {
        try await request("/admin/evals/ingest/red-team", method: "GET")
    }

    func adminReports(status: String? = nil, targetType: String? = nil) async throws -> [AdminReport] {
        var query: [URLQueryItem] = []
        if let status {
            query.append(URLQueryItem(name: "status", value: status))
        }
        if let targetType {
            query.append(URLQueryItem(name: "type", value: targetType))
        }
        return try await request("/admin/reports", method: "GET", query: query)
    }

    func resolveAdminReport(reportID: String, status: String, notes: String? = nil) async throws {
        try await requestEmpty(
            "/admin/reports/\(reportID.urlPathEscaped)/resolve",
            method: "POST",
            body: AdminReportResolveRequest(status: status, notes: notes)
        )
    }

    func adminVideos(moderationStatus: String? = nil) async throws -> [FeedVideo] {
        let query = moderationStatus.map {
            [URLQueryItem(name: "moderation_status", value: $0)]
        } ?? []
        return try await request("/admin/videos", method: "GET", query: query)
    }

    func adminComments(moderationStatus: String? = nil) async throws -> [Comment] {
        let query = moderationStatus.map {
            [URLQueryItem(name: "moderation_status", value: $0)]
        } ?? []
        return try await request("/admin/comments", method: "GET", query: query)
    }

    func moderateAdminVideo(videoID: String, status: String, notes: String? = nil) async throws {
        try await requestEmpty(
            "/admin/videos/\(videoID.urlPathEscaped)/moderation",
            method: "PATCH",
            body: AdminModerationUpdateRequest(status: status, notes: notes)
        )
    }

    func moderateAdminComment(commentID: String, status: String, notes: String? = nil) async throws {
        try await requestEmpty(
            "/admin/comments/\(commentID.urlPathEscaped)/moderation",
            method: "PATCH",
            body: AdminModerationUpdateRequest(status: status, notes: notes)
        )
    }

    private func request<T: Decodable>(_ path: String, method: String, query: [URLQueryItem] = []) async throws -> T {
        let request = try makeRequest(path: path, method: method, query: query, body: Optional<Data>.none)
        return try await execute(request)
    }

    private func request<T: Decodable, Body: Encodable>(_ path: String, method: String, query: [URLQueryItem] = [], body: Body) async throws -> T {
        let data = try encoder.encode(body)
        let request = try makeRequest(path: path, method: method, query: query, body: data)
        return try await execute(request)
    }

    private func requestEmpty(_ path: String, method: String, query: [URLQueryItem] = []) async throws {
        let request = try makeRequest(path: path, method: method, query: query, body: Optional<Data>.none)
        let _: APIEmptyResponse = try await execute(request)
    }

    private func requestEmpty<Body: Encodable>(_ path: String, method: String, query: [URLQueryItem] = [], body: Body) async throws {
        let data = try encoder.encode(body)
        let request = try makeRequest(path: path, method: method, query: query, body: data)
        let _: APIEmptyResponse = try await execute(request)
    }

    private func makeRequest(path: String, method: String, query: [URLQueryItem], body: Data?) throws -> URLRequest {
        guard var components = URLComponents(url: baseURL.appendingPathComponent(path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))), resolvingAgainstBaseURL: false) else {
            throw APIClientError.invalidURL
        }
        if !query.isEmpty {
            components.queryItems = query
        }
        guard let url = components.url else {
            throw APIClientError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        if let bearerToken {
            request.setValue("Bearer \(bearerToken)", forHTTPHeaderField: "Authorization")
        }
        if let body {
            request.httpBody = body
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        return request
    }

    private func execute<T: Decodable>(_ request: URLRequest) async throws -> T {
        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIClientError.invalidResponse
        }

        guard (200..<300).contains(httpResponse.statusCode) else {
            let apiError = try? decoder.decode(APIErrorResponse.self, from: data)
            let message = apiError?.detail ?? apiError?.message ?? HTTPURLResponse.localizedString(forStatusCode: httpResponse.statusCode)
            throw APIClientError.server(statusCode: httpResponse.statusCode, message: message)
        }

        if data.isEmpty, T.self == APIEmptyResponse.self {
            return APIEmptyResponse() as! T
        }

        return try decoder.decode(T.self, from: data)
    }
}

private extension String {
    var urlPathEscaped: String {
        addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? self
    }
}

import Foundation

struct APIEmptyResponse: Codable {}

struct APIErrorResponse: Codable {
    var detail: String?
    var message: String?
}

struct User: Codable, Identifiable {
    var id: String
    var username: String
    var email: String
    var displayName: String?
    var avatarURL: URL?
    var onboardingCompleted: Bool
    var isAdmin: Bool?
    var createdAt: Date?

    enum CodingKeys: String, CodingKey {
        case id
        case username
        case email
        case displayName
        case avatarURL = "avatarUrl"
        case onboardingCompleted
        case isAdmin
        case createdAt
    }
}

struct AuthResponse: Codable {
    var accessToken: String
    var tokenType: String?
    var user: User
}

struct LoginRequest: Codable {
    var email: String
    var password: String
}

struct RegisterRequest: Codable {
    var username: String
    var email: String
    var password: String
    var birthday: String?
}

struct AppleAuthRequest: Codable {
    var identityToken: String?
    var authorizationCode: String?
}

struct OnboardingRequest: Codable {
    var topics: [String]
    var intensity: String
}

struct Topic: Codable, Identifiable, Hashable {
    var id: String { slug }
    var slug: String
    var name: String
    var description: String?
    var isFollowed: Bool?
}

struct CreatorSummary: Codable, Identifiable, Hashable {
    var id: String
    var source: String?
    var handle: String?
    var displayName: String?
    var youtubeChannelID: String?
    var avatarURL: URL?
    var isFollowed: Bool?
    var isBlocked: Bool?

    enum CodingKeys: String, CodingKey {
        case id
        case source
        case handle
        case displayName
        case youtubeChannelID = "youtubeChannelId"
        case avatarURL = "avatarUrl"
        case isFollowed
        case isBlocked
    }

    var feedName: String {
        displayName ?? handle ?? "creator"
    }
}

enum FeedItemType: String, Codable {
    case video
    case reflection
}

struct FeedResponse: Decodable {
    var items: [FeedItem]
    var nextCursor: String?
}

struct FeedItem: Decodable, Identifiable {
    var id: String
    var itemType: FeedItemType
    var video: FeedVideo?
    var reflection: ReflectionCard?
    var impressionID: String?
    var reason: String?
    var isLiked: Bool?
    var isSaved: Bool?
    var isCreatorFollowed: Bool?

    enum CodingKeys: String, CodingKey {
        case id
        case itemType = "type"
        case video
        case reflection
        case impressionID = "impressionId"
        case reason = "rankReason"
        case isLiked
        case isSaved
        case isCreatorFollowed
    }

    init(
        id: String,
        itemType: FeedItemType,
        video: FeedVideo?,
        reflection: ReflectionCard?,
        impressionID: String?,
        reason: String?,
        isLiked: Bool?,
        isSaved: Bool?,
        isCreatorFollowed: Bool?
    ) {
        self.id = id
        self.itemType = itemType
        self.video = video
        self.reflection = reflection
        self.impressionID = impressionID
        self.reason = reason
        self.isLiked = isLiked
        self.isSaved = isSaved
        self.isCreatorFollowed = isCreatorFollowed
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        itemType = try container.decode(FeedItemType.self, forKey: .itemType)
        video = try container.decodeIfPresent(FeedVideo.self, forKey: .video)
        reflection = try container.decodeIfPresent(ReflectionCard.self, forKey: .reflection)
        impressionID = try container.decodeIfPresent(String.self, forKey: .impressionID)
        reason = try container.decodeIfPresent(String.self, forKey: .reason)
        isLiked = try container.decodeIfPresent(Bool.self, forKey: .isLiked)
        isSaved = try container.decodeIfPresent(Bool.self, forKey: .isSaved)
        isCreatorFollowed = try container.decodeIfPresent(Bool.self, forKey: .isCreatorFollowed)
        id = try container.decodeIfPresent(String.self, forKey: .id)
            ?? video?.id
            ?? reflection?.id
            ?? "\(itemType.rawValue)-\(UUID().uuidString)"
    }
}

struct FeedVideo: Codable, Identifiable {
    var id: String
    var youtubeVideoID: String
    var title: String
    var description: String?
    var creator: CreatorSummary?
    var thumbnailURL: URL?
    var sourceURL: URL?
    var embedURL: URL?
    var durationSeconds: Int?
    var tags: [String]?
    var topics: [String]?
    var moderationStatus: String?
    var spiritualScore: Double?
    var theologyScore: Double?
    var entertainmentScore: Double?
    var freshnessScore: Double?

    enum CodingKeys: String, CodingKey {
        case id
        case youtubeVideoID = "youtubeVideoId"
        case title
        case description
        case creator
        case thumbnailURL = "thumbnailUrl"
        case sourceURL = "sourceUrl"
        case embedURL = "embedUrl"
        case durationSeconds
        case tags
        case topics
        case moderationStatus
        case spiritualScore
        case theologyScore
        case entertainmentScore
        case freshnessScore
    }
}

struct ReflectionCard: Codable, Identifiable {
    var id: String
    var title: String
    var scriptureReference: String
    var body: String
    var prompt: String
    var trigger: String?
}

enum VideoWatchEventKind: String, Codable {
    case start
    case pause
    case complete
    case skip
    case rewatch
}

struct FeedImpressionRequest: Codable {
    var videoID: String
    var position: Int
}

struct VideoWatchRequest: Codable {
    var secondsWatched: Double
    var percentComplete: Double
    var rewatched: Bool
    var eventType: VideoWatchEventKind
}

struct Comment: Codable, Identifiable {
    var id: String
    var videoID: String
    var author: User?
    var body: String
    var moderationStatus: String?
    var createdAt: Date?

    enum CodingKeys: String, CodingKey {
        case id
        case videoID = "videoId"
        case author
        case body
        case moderationStatus
        case createdAt
    }
}

struct CreateCommentRequest: Codable {
    var body: String
}

struct ReportRequest: Codable {
    var reason: String
    var details: String?
}

struct NotInterestedRequest: Codable {
    var reason: String?
}

struct SearchResponse: Codable {
    var videos: [FeedVideo]?
    var creators: [CreatorSummary]?
    var topics: [Topic]?
}

struct FollowRequest: Codable {
    var source: String
}

enum BibleMaxxingTopics {
    static let onboarding: [Topic] = [
        Topic(slug: "prayer", name: "Prayer", description: nil, isFollowed: nil),
        Topic(slug: "anxiety", name: "Anxiety", description: nil, isFollowed: nil),
        Topic(slug: "discipline", name: "Discipline", description: nil, isFollowed: nil),
        Topic(slug: "apologetics", name: "Apologetics", description: nil, isFollowed: nil),
        Topic(slug: "workplace-holiness", name: "Workplace holiness", description: nil, isFollowed: nil),
        Topic(slug: "bible-study", name: "Bible study", description: nil, isFollowed: nil),
        Topic(slug: "worship", name: "Worship", description: nil, isFollowed: nil),
        Topic(slug: "testimony", name: "Testimony", description: nil, isFollowed: nil),
        Topic(slug: "christian-living", name: "Christian living", description: nil, isFollowed: nil),
        Topic(slug: "scripture", name: "Scripture", description: nil, isFollowed: nil),
        Topic(slug: "theology", name: "Theology", description: nil, isFollowed: nil),
        Topic(slug: "gospel-encouragement", name: "Gospel encouragement", description: nil, isFollowed: nil)
    ]
}

enum SampleData {
    static let fallbackFeed: [FeedItem] = [
        FeedItem(
            id: "sample-reflection-1",
            itemType: .reflection,
            video: nil,
            reflection: ReflectionCard(
                id: "sample-reflection-1",
                title: "Pause before the next swipe",
                scriptureReference: "Colossians 3:17",
                body: "Whatever you do, receive it as a chance to belong to Christ in the ordinary details.",
                prompt: "Name one work or life moment today where you want to be more like Him.",
                trigger: "sample"
            ),
            impressionID: nil,
            reason: "Reflection cards interrupt binge-like loops.",
            isLiked: nil,
            isSaved: nil,
            isCreatorFollowed: nil
        )
    ]
}

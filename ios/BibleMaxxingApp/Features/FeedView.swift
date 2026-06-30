import SwiftUI

struct FeedView: View {
    @EnvironmentObject private var session: SessionStore
    @StateObject private var viewModel = FeedViewModel()
    @State private var showSettings = false

    var body: some View {
        ZStack(alignment: .top) {
            Color.black.ignoresSafeArea()

            if viewModel.isLoading && viewModel.items.isEmpty {
                ProgressView("Loading feed")
                    .tint(.white)
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView(.vertical) {
                    LazyVStack(spacing: 0) {
                        ForEach(viewModel.items) { item in
                            FeedItemPage(
                                item: item,
                                isActive: item.id == viewModel.currentItemID,
                                viewModel: viewModel
                            )
                            .containerRelativeFrame([.horizontal, .vertical])
                            .id(item.id)
                        }
                    }
                    .scrollTargetLayout()
                }
                .scrollTargetBehavior(.viewAligned(limitBehavior: .always))
                .scrollIndicators(.hidden)
                .scrollPosition(id: $viewModel.currentItemID)
                .ignoresSafeArea()
                .background(Color.black)
            }

            FeedChrome(
                errorMessage: viewModel.errorMessage,
                onRefresh: {
                    Task { await viewModel.reload(using: session.apiClient) }
                },
                onSettings: {
                    showSettings = true
                }
            )
        }
        .task {
            await viewModel.load(using: session.apiClient)
        }
        .onChange(of: viewModel.currentItemID) { _, newValue in
            Task { await viewModel.recordCurrentItemStart(newValue) }
        }
        .sheet(item: $viewModel.commentsVideo) { video in
            CommentsSheet(video: video)
                .environmentObject(session)
        }
        .sheet(item: $viewModel.pendingReport) { target in
            ReportSheet(target: target) { reason, notes in
                await viewModel.submitReport(target: target, reason: reason, notes: notes)
            }
        }
        .sheet(isPresented: $showSettings) {
            SettingsView()
                .environmentObject(session)
        }
    }
}

private struct FeedChrome: View {
    let errorMessage: String?
    let onRefresh: () -> Void
    let onSettings: () -> Void

    var body: some View {
        VStack(spacing: 8) {
            HStack {
                Button(action: onRefresh) {
                    Image(systemName: "arrow.clockwise")
                        .font(.headline)
                        .frame(width: 42, height: 42)
                        .background(.black.opacity(0.35), in: Circle())
                }
                .accessibilityLabel("Refresh feed")

                Spacer()

                Text("BibleMaxxing")
                    .font(.headline.weight(.black))
                    .shadow(radius: 8)

                Spacer()

                Button(action: onSettings) {
                    Image(systemName: "person.crop.circle")
                        .font(.title2)
                        .frame(width: 42, height: 42)
                        .background(.black.opacity(0.35), in: Circle())
                }
                .accessibilityLabel("Settings")
            }
            .foregroundStyle(.white)
            .padding(.horizontal, 16)
            .padding(.top, 10)

            if let errorMessage {
                Text(errorMessage)
                    .font(.caption.weight(.medium))
                    .foregroundStyle(.white)
                    .lineLimit(2)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(.black.opacity(0.62), in: RoundedRectangle(cornerRadius: 8))
                    .padding(.horizontal, 16)
            }
        }
    }
}

private struct FeedItemPage: View {
    let item: FeedItem
    let isActive: Bool
    @ObservedObject var viewModel: FeedViewModel

    var body: some View {
        if let video = item.video {
            VideoFeedPage(
                item: item,
                video: video,
                isActive: isActive,
                viewModel: viewModel
            )
        } else if let reflection = item.reflection {
            ReflectionFeedPage(reflection: reflection)
        } else {
            EmptyFeedPage()
        }
    }
}

private struct VideoFeedPage: View {
    let item: FeedItem
    let video: FeedVideo
    let isActive: Bool
    @ObservedObject var viewModel: FeedViewModel
    @EnvironmentObject private var session: SessionStore

    var body: some View {
        GeometryReader { proxy in
            ZStack(alignment: .bottom) {
                Group {
                    if viewModel.isPrepared(itemID: item.id) {
                        ZStack {
                            YouTubePlayerView(
                                videoID: video.youtubeVideoID,
                                playerURL: session.apiClient.youtubePlayerPageURL(
                                    videoID: video.youtubeVideoID,
                                    autoplay: isActive && viewModel.didTapStart
                                ),
                                isActive: isActive,
                                shouldAutoplay: viewModel.didTapStart
                            )
                            .allowsHitTesting(false)

                            if !viewModel.didTapStart {
                                ThumbnailPlaceholder(url: video.thumbnailURL)
                                    .allowsHitTesting(false)
                            }
                        }
                    } else {
                        ThumbnailPlaceholder(url: video.thumbnailURL)
                    }
                }
                .frame(width: proxy.size.width, height: proxy.size.height)
                .clipped()

                LinearGradient(
                    colors: [.clear, .black.opacity(0.38), .black.opacity(0.9)],
                    startPoint: .top,
                    endPoint: .bottom
                )
                .frame(height: min(360, proxy.size.height * 0.56))
                .allowsHitTesting(false)

                HStack(alignment: .bottom, spacing: 12) {
                    VideoMetadataView(video: video, item: item) { slug in
                        Task { await viewModel.followTopic(slug) }
                    }
                    .frame(maxWidth: max(210, proxy.size.width - 104), alignment: .leading)

                    Spacer(minLength: 6)

                    ActionRail(
                        isLiked: item.isLiked ?? false,
                        isSaved: item.isSaved ?? false,
                        isCreatorFollowed: item.isCreatorFollowed ?? video.creator?.isFollowed ?? false,
                        onLike: { Task { await viewModel.toggleLike(itemID: item.id) } },
                        onSave: { Task { await viewModel.toggleSave(itemID: item.id) } },
                        onComment: { viewModel.commentsVideo = video },
                        onNotInterested: { Task { await viewModel.markNotInterested(itemID: item.id) } },
                        onReport: { viewModel.pendingReport = .video(video) },
                        onBlock: { Task { await viewModel.blockCreator(for: item.id) } },
                        onFollowCreator: { Task { await viewModel.toggleCreatorFollow(itemID: item.id) } }
                    )
                }
                .padding(.horizontal, 14)
                .padding(.bottom, 54)

                if isActive && !viewModel.didTapStart {
                    TapToStartOverlay {
                        Task { await viewModel.startPlayback() }
                    }
                    .frame(width: proxy.size.width, height: proxy.size.height, alignment: .center)
                }
            }
        }
        .contentShape(Rectangle())
        .onTapGesture(count: 2) {
            Task { await viewModel.toggleLike(itemID: item.id) }
        }
    }
}

private struct VideoMetadataView: View {
    let video: FeedVideo
    let item: FeedItem
    let onFollowTopic: (String) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(displayTitle)
                .font(.title3.weight(.bold))
                .lineLimit(3)
                .shadow(radius: 8)

            HStack(spacing: 8) {
                Text(creatorText)
                    .font(.subheadline.weight(.semibold))

                if let sourceURL = video.sourceURL {
                    Link(destination: sourceURL) {
                        Label("YouTube", systemImage: "play.rectangle")
                            .font(.caption.weight(.semibold))
                    }
                    .foregroundStyle(.white.opacity(0.82))
                }
            }

            if let reason = displayReason {
                Text(reason)
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.78))
                    .lineLimit(2)
            }

            let topics = displayTopics
            if !topics.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(topics, id: \.slug) { topic in
                            Button {
                                onFollowTopic(topic.slug)
                            } label: {
                                Label(topic.name, systemImage: "plus")
                                    .font(.caption.weight(.bold))
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 7)
                                    .background(.white.opacity(0.16), in: Capsule())
                            }
                            .buttonStyle(.plain)
                            .accessibilityLabel("Follow topic \(topic.name)")
                        }
                    }
                }
            }
        }
        .foregroundStyle(.white)
        .frame(maxWidth: 310, alignment: .leading)
    }

    private var displayTitle: String {
        let withoutHashtags = video.title.replacingOccurrences(
            of: #"\s*#\S+"#,
            with: "",
            options: .regularExpression
        )
        return withoutHashtags.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var creatorText: String {
        if let handle = video.creator?.handle?.cleanHandle, !handle.isEmpty {
            return "@\(handle)"
        }
        return video.creator?.displayName ?? "Creator"
    }

    private var displayReason: String? {
        guard let reason = item.reason?.lowercased(), !reason.isEmpty else { return nil }
        if reason.contains("pause") || reason.contains("scroll") {
            return "A short pause to refocus on Christ."
        }
        return "Recommended for your walk with Christ."
    }

    private var displayTopics: [DisplayTopic] {
        (video.topics ?? [])
            .prefix(4)
            .map { DisplayTopic(slug: $0, name: $0.topicDisplayName) }
    }
}

private struct DisplayTopic: Hashable {
    let slug: String
    let name: String
}

private struct TapToStartOverlay: View {
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 12) {
                Image(systemName: "speaker.wave.2.circle.fill")
                    .font(.system(size: 56, weight: .semibold))
                Text("Tap to start")
                    .font(.title2.weight(.black))
                Text("Sound begins after your tap. Swiping will continue playback.")
                    .font(.footnote.weight(.medium))
                    .multilineTextAlignment(.center)
                    .foregroundStyle(.white.opacity(0.82))
            }
            .padding(24)
            .frame(maxWidth: 270)
            .background(.black.opacity(0.66), in: RoundedRectangle(cornerRadius: 8))
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(.white.opacity(0.22))
            )
        }
        .buttonStyle(.plain)
        .foregroundStyle(.white)
        .accessibilityLabel("Tap to start feed playback")
    }
}

private struct ThumbnailPlaceholder: View {
    let url: URL?

    var body: some View {
        ZStack {
            Color.black
            AsyncImage(url: url) { phase in
                switch phase {
                case let .success(image):
                    image
                        .resizable()
                        .scaledToFill()
                        .blur(radius: 10)
                        .overlay(Color.black.opacity(0.45))
                default:
                    Rectangle()
                        .fill(Color.white.opacity(0.08))
                }
            }
            Image(systemName: "play.rectangle.fill")
                .font(.system(size: 62))
                .foregroundStyle(.white.opacity(0.8))
        }
        .clipped()
    }
}

private struct ReflectionFeedPage: View {
    let reflection: ReflectionCard

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            VStack(alignment: .leading, spacing: 22) {
                Text(reflection.title)
                    .font(.largeTitle.weight(.black))
                Text(reflection.scriptureReference)
                    .font(.headline.weight(.bold))
                    .foregroundStyle(.yellow)
                Text(reflection.body)
                    .font(.title3)
                    .foregroundStyle(.white.opacity(0.86))
                Text(reflection.prompt)
                    .font(.headline)
                    .padding(16)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(.white.opacity(0.08), in: RoundedRectangle(cornerRadius: 8))
                if let trigger = reflection.trigger {
                    Text("Paused after \(trigger).")
                        .font(.caption.weight(.medium))
                        .foregroundStyle(.secondary)
                }
            }
            .padding(28)
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .foregroundStyle(.white)
    }
}

private struct EmptyFeedPage: View {
    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            Text("This feed item is unavailable.")
                .foregroundStyle(.secondary)
        }
    }
}

struct CommentsSheet: View {
    @EnvironmentObject private var session: SessionStore
    let video: FeedVideo

    @State private var comments: [Comment] = []
    @State private var draft = ""
    @State private var isLoading = true
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if isLoading {
                    ProgressView("Loading comments")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if comments.isEmpty {
                    ContentUnavailableView("No comments yet", systemImage: "bubble.right", description: Text("Start a thoughtful conversation."))
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List(comments) { comment in
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text(comment.author?.username ?? "User")
                                    .font(.subheadline.weight(.bold))
                                Spacer()
                                Button(role: .destructive) {
                                    Task { await report(comment) }
                                } label: {
                                    Label("Report", systemImage: "flag")
                                }
                                .labelStyle(.iconOnly)
                            }
                            Text(comment.body)
                                .font(.body)
                            Text(comment.statusText)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        .padding(.vertical, 6)
                    }
                    .scrollContentBackground(.hidden)
                }

                if let errorMessage {
                    Text(errorMessage)
                        .font(.caption.weight(.medium))
                        .foregroundStyle(.red)
                        .padding(.horizontal)
                        .padding(.bottom, 8)
                }

                HStack(spacing: 10) {
                    TextField(text: $draft, axis: .vertical) {
                        Text("Add a thoughtful comment")
                            .foregroundStyle(.white.opacity(0.48))
                    }
                        .lineLimit(1...4)
                        .textInputAutocapitalization(.sentences)
                        .autocorrectionDisabled(false)
                        .foregroundStyle(.white)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 10)
                        .background(.white.opacity(0.09), in: RoundedRectangle(cornerRadius: 8))
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(.white.opacity(0.12))
                        )
                    Button {
                        Task { await submitComment() }
                    } label: {
                        Image(systemName: "paperplane.fill")
                    }
                    .disabled(draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
                .padding()
                .background(.black.opacity(0.12))
            }
            .navigationTitle("Comments")
            .navigationBarTitleDisplayMode(.inline)
            .task { await loadComments() }
        }
        .preferredColorScheme(.dark)
    }

    private func loadComments() async {
        isLoading = true
        defer { isLoading = false }

        do {
            comments = try await session.apiClient.comments(videoID: video.id)
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func submitComment() async {
        let body = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !body.isEmpty else { return }

        do {
            let comment = try await session.apiClient.addComment(videoID: video.id, body: body)
            comments.insert(comment, at: 0)
            draft = ""
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func report(_ comment: Comment) async {
        do {
            try await session.apiClient.reportComment(commentID: comment.id, reason: "reported_from_comment_sheet", notes: nil)
            errorMessage = "Report sent. Thank you for helping keep the feed safe."
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct ReportSheet: View {
    let target: ReportTarget
    let onSubmit: (String, String?) async -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var reason = "theological_safety"
    @State private var notes = ""
    @State private var isSubmitting = false

    private let reasons = [
        ("theological_safety", "Theological safety"),
        ("not_christ_centered", "Not Christ-centered"),
        ("harassment_or_hate", "Harassment or hate"),
        ("sexual_or_violent", "Sexual or violent"),
        ("spam_or_engagement_bait", "Spam or bait"),
        ("other", "Other")
    ]

    var body: some View {
        NavigationStack {
            Form {
                Section("Target") {
                    Text(target.title)
                }

                Section("Reason") {
                    Picker("Reason", selection: $reason) {
                        ForEach(reasons, id: \.0) { value, label in
                            Text(label).tag(value)
                        }
                    }
                }

                Section("Notes") {
                    TextEditor(text: $notes)
                        .frame(minHeight: 110)
                }
            }
            .navigationTitle("Report")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Send") {
                        Task {
                            isSubmitting = true
                            await onSubmit(reason, notes.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : notes)
                            isSubmitting = false
                            dismiss()
                        }
                    }
                    .disabled(isSubmitting)
                }
            }
        }
        .preferredColorScheme(.dark)
    }
}

struct ReportTarget: Identifiable {
    enum Kind {
        case video
        case comment
    }

    let id = UUID()
    let kind: Kind
    let resourceID: String
    let title: String

    static func video(_ video: FeedVideo) -> ReportTarget {
        ReportTarget(kind: .video, resourceID: video.id, title: video.title)
    }

    static func comment(_ comment: Comment) -> ReportTarget {
        ReportTarget(kind: .comment, resourceID: comment.id, title: comment.body)
    }
}

private extension Comment {
    var statusText: String {
        guard let moderationStatus, !moderationStatus.isEmpty else {
            return "Under review"
        }

        switch moderationStatus {
        case "approved":
            return "Visible"
        case "hidden":
            return "Hidden"
        default:
            return "Under review"
        }
    }
}

private extension String {
    var cleanHandle: String {
        trimmingCharacters(in: .whitespacesAndNewlines)
            .trimmingCharacters(in: CharacterSet(charactersIn: "@"))
    }

    var topicDisplayName: String {
        split(separator: "-")
            .map { word in
                let lowered = word.lowercased()
                return lowered.prefix(1).uppercased() + String(lowered.dropFirst())
            }
            .joined(separator: " ")
    }
}

@MainActor
final class FeedViewModel: ObservableObject {
    @Published var items: [FeedItem] = []
    @Published var currentItemID: String?
    @Published var didTapStart = false
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var commentsVideo: FeedVideo?
    @Published var pendingReport: ReportTarget?

    private var apiClient: APIClient?
    private var hasLoaded = false
    private var sessionStartedAt = Date()
    private var reflectionInserted = false

    func load(using apiClient: APIClient) async {
        guard !hasLoaded else { return }
        self.apiClient = apiClient
        await reload(using: apiClient)
        hasLoaded = true
    }

    func reload(using apiClient: APIClient) async {
        self.apiClient = apiClient
        isLoading = true
        defer { isLoading = false }

        do {
            let response = try await apiClient.fetchFeed()
            items = response.items.filter { item in
                item.itemType == .reflection || item.video?.youtubeVideoID.isEmpty == false
            }
            errorMessage = nil

            if items.isEmpty {
                items = SampleData.fallbackFeed
                errorMessage = "We couldn't load new videos. Showing a reflection while we reconnect."
            }

            currentItemID = items.first?.id
            await recordCurrentItemStart(currentItemID)
        } catch {
            items = SampleData.fallbackFeed
            currentItemID = items.first?.id
            errorMessage = "We couldn't load new videos. Showing a reflection while we reconnect."
        }
    }

    func startPlayback() async {
        didTapStart = true
        await recordCurrentItemStart(currentItemID)
    }

    func recordCurrentItemStart(_ itemID: String?) async {
        guard let itemID, let itemIndex = index(for: itemID) else { return }
        let item = items[itemIndex]

        maybeInsertReflection(after: itemID)

        if let video = item.video {
            await recordImpression(videoID: video.id, position: itemIndex)
            if didTapStart {
                await recordWatch(videoID: video.id, secondsWatched: 0, percentComplete: 0, rewatched: false, eventType: .start)
            }
        }
    }

    func isPrepared(itemID: String) -> Bool {
        preparedItemIDs.contains(itemID)
    }

    func toggleLike(itemID: String) async {
        guard let index = index(for: itemID), let video = items[index].video else { return }
        let newValue = !(items[index].isLiked ?? false)
        items[index].isLiked = newValue

        do {
            try await apiClient?.setLike(videoID: video.id, liked: newValue)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func toggleSave(itemID: String) async {
        guard let index = index(for: itemID), let video = items[index].video else { return }
        let newValue = !(items[index].isSaved ?? false)
        items[index].isSaved = newValue

        do {
            try await apiClient?.setSave(videoID: video.id, saved: newValue)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func markNotInterested(itemID: String) async {
        guard let index = index(for: itemID), let video = items[index].video else { return }
        items.remove(at: index)
        currentItemID = items.isEmpty ? nil : items[min(index, items.count - 1)].id

        await recordWatch(
            videoID: video.id,
            secondsWatched: 0,
            percentComplete: 0,
            rewatched: false,
            eventType: .skip
        )

        do {
            try await apiClient?.markNotInterested(videoID: video.id, reason: "not_interested")
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func toggleCreatorFollow(itemID: String) async {
        guard let index = index(for: itemID), let creator = items[index].video?.creator else { return }
        guard !(items[index].isCreatorFollowed ?? creator.isFollowed ?? false) else {
            errorMessage = "Already following \(creator.feedName)."
            return
        }

        for itemIndex in items.indices where items[itemIndex].video?.creator?.id == creator.id {
            items[itemIndex].isCreatorFollowed = true
            items[itemIndex].video?.creator?.isFollowed = true
        }

        do {
            try await apiClient?.followCreator(creatorID: creator.id)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func followTopic(_ slug: String) async {
        do {
            try await apiClient?.followTopic(slug: slug)
            errorMessage = "Following \(slug.topicDisplayName)."
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func blockCreator(for itemID: String) async {
        guard let creator = items.first(where: { $0.id == itemID })?.video?.creator else { return }
        items.removeAll { $0.video?.creator?.id == creator.id }
        currentItemID = items.first?.id

        do {
            try await apiClient?.blockCreator(creatorID: creator.id)
            errorMessage = "Blocked \(creator.feedName)."
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func submitReport(target: ReportTarget, reason: String, notes: String?) async {
        do {
            switch target.kind {
            case .video:
                try await apiClient?.reportVideo(videoID: target.resourceID, reason: reason, notes: notes)
            case .comment:
                try await apiClient?.reportComment(commentID: target.resourceID, reason: reason, notes: notes)
            }
            errorMessage = "Report sent. Thank you for helping keep the feed safe."
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private var preparedItemIDs: Set<String> {
        guard let currentItemID, let currentIndex = index(for: currentItemID) else {
            return Set(items.prefix(2).map(\.id))
        }

        let lowerBound = max(items.startIndex, currentIndex - 1)
        let upperBound = min(items.index(before: items.endIndex), currentIndex + 1)
        return Set(items[lowerBound...upperBound].map(\.id))
    }

    private func maybeInsertReflection(after itemID: String) {
        guard !reflectionInserted, let currentIndex = index(for: itemID) else { return }

        let elapsed = Date().timeIntervalSince(sessionStartedAt)
        let bingeLike = currentIndex >= 9
        guard elapsed >= 600 || bingeLike else { return }

        reflectionInserted = true
        let trigger = elapsed >= 600 ? "about 10 minutes of feed time" : "several quick swipes"
        let reflection = ReflectionCard(
            id: "reflection-\(UUID().uuidString)",
            title: "Let this become prayer",
            scriptureReference: "Romans 12:2",
            body: "The goal is not just cleaner scrolling. It is a mind renewed around Christ.",
            prompt: "Before the next video, ask God for one concrete act of obedience today.",
            trigger: trigger
        )
        let item = FeedItem(
            id: reflection.id,
            itemType: .reflection,
            video: nil,
            reflection: reflection,
            impressionID: nil,
            reason: "Anti-addiction reflection card",
            isLiked: nil,
            isSaved: nil,
            isCreatorFollowed: nil
        )
        items.insert(item, at: min(currentIndex + 1, items.endIndex))
    }

    private func recordImpression(videoID: String, position: Int) async {
        do {
            try await apiClient?.recordFeedImpression(videoID: videoID, position: position)
        } catch {
            // Feed telemetry should never block the feed.
        }
    }

    private func recordWatch(videoID: String, secondsWatched: Double, percentComplete: Double, rewatched: Bool, eventType: VideoWatchEventKind) async {
        do {
            try await apiClient?.recordWatch(
                videoID: videoID,
                secondsWatched: secondsWatched,
                percentComplete: percentComplete,
                rewatched: rewatched,
                eventType: eventType
            )
        } catch {
            // Watch telemetry should never block the feed.
        }
    }

    private func index(for itemID: String) -> Int? {
        items.firstIndex { $0.id == itemID }
    }
}

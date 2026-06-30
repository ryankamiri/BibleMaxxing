import Foundation
import SwiftUI

struct AdminView: View {
    @EnvironmentObject private var session: SessionStore
    @StateObject private var viewModel = AdminViewModel()

    var body: some View {
        Group {
            if session.currentUser?.isAdmin == true {
                adminContent
            } else {
                ContentUnavailableView(
                    "Admin access required",
                    systemImage: "lock.shield",
                    description: Text("This area is only available to BibleMaxxing admins.")
                )
                .foregroundStyle(.white)
            }
        }
        .background(Color.black.ignoresSafeArea())
        .navigationTitle("Admin")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    Task { await viewModel.reload(using: session.apiClient) }
                } label: {
                    if viewModel.isLoading {
                        ProgressView()
                            .controlSize(.small)
                    } else {
                        Image(systemName: "arrow.clockwise")
                    }
                }
                .disabled(viewModel.isLoading || session.currentUser?.isAdmin != true)
                .accessibilityLabel("Refresh admin dashboard")
            }
        }
        .task {
            guard session.currentUser?.isAdmin == true else { return }
            await viewModel.load(using: session.apiClient)
        }
        .preferredColorScheme(.dark)
    }

    private var adminContent: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                AdminPageHeader(lastLoadedAt: viewModel.lastLoadedAt)

                if viewModel.isLoading && !viewModel.hasLoaded {
                    ProgressView("Loading admin data")
                        .tint(.white)
                        .foregroundStyle(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 60)
                } else {
                    AdminSnapshotGrid(
                        reportCount: viewModel.openReports.count,
                        videoCount: viewModel.pendingVideos.count,
                        commentCount: viewModel.pendingComments.count
                    )

                    if let statusMessage = viewModel.statusMessage {
                        AdminNotice(text: statusMessage, systemImage: "checkmark.circle", tint: .green)
                    }

                    if let errorMessage = viewModel.errorMessage {
                        AdminNotice(text: errorMessage, systemImage: "exclamationmark.triangle", tint: .red)
                    }

                    AdminScorecardsSection(scorecards: viewModel.scorecards)

                    AdminReportsSection(viewModel: viewModel)

                    AdminVideosSection(viewModel: viewModel)

                    AdminCommentsSection(viewModel: viewModel)
                }
            }
            .padding(.horizontal, 16)
            .padding(.top, 18)
            .padding(.bottom, 32)
        }
        .refreshable {
            await viewModel.reload(using: session.apiClient)
        }
    }
}

private struct AdminPageHeader: View {
    let lastLoadedAt: Date?

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("Mobile admin", systemImage: "shield.lefthalf.filled")
                .font(.title2.weight(.bold))
                .foregroundStyle(.white)

            Text(lastLoadedAt.map { "Updated \($0.adminRelativeText)" } ?? "Ready to review today's queues.")
                .font(.subheadline)
                .foregroundStyle(.white.opacity(0.68))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

private struct AdminSnapshotGrid: View {
    let reportCount: Int
    let videoCount: Int
    let commentCount: Int

    private let columns = [
        GridItem(.flexible(), spacing: 10),
        GridItem(.flexible(), spacing: 10),
        GridItem(.flexible(), spacing: 10)
    ]

    var body: some View {
        LazyVGrid(columns: columns, spacing: 10) {
            AdminCountTile(title: "Reports", count: reportCount, systemImage: "flag.fill", tint: .orange)
            AdminCountTile(title: "Videos", count: videoCount, systemImage: "play.rectangle.fill", tint: .cyan)
            AdminCountTile(title: "Comments", count: commentCount, systemImage: "bubble.left.and.bubble.right.fill", tint: .purple)
        }
    }
}

private struct AdminCountTile: View {
    let title: String
    let count: Int
    let systemImage: String
    let tint: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Image(systemName: systemImage)
                .font(.headline)
                .foregroundStyle(tint)

            Text("\(count)")
                .font(.system(size: 28, weight: .black, design: .rounded))
                .foregroundStyle(.white)

            Text(title)
                .font(.caption.weight(.semibold))
                .foregroundStyle(.white.opacity(0.68))
        }
        .frame(maxWidth: .infinity, minHeight: 100, alignment: .leading)
        .padding(12)
        .background(.white.opacity(0.07), in: RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(.white.opacity(0.1))
        )
    }
}

private struct AdminNotice: View {
    let text: String
    let systemImage: String
    let tint: Color

    var body: some View {
        Label(text, systemImage: systemImage)
            .font(.footnote.weight(.semibold))
            .foregroundStyle(.white)
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(tint.opacity(0.16), in: RoundedRectangle(cornerRadius: 8))
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(tint.opacity(0.28))
            )
    }
}

private struct AdminScorecardsSection: View {
    let scorecards: [AdminEvalScorecard]

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            AdminSectionHeader(
                title: "Eval scorecards",
                subtitle: "Recommendation quality and ingest safety",
                systemImage: "chart.line.uptrend.xyaxis"
            )

            if scorecards.isEmpty {
                AdminEmptyState(title: "No eval runs loaded", systemImage: "chart.bar")
            } else {
                ForEach(scorecards) { scorecard in
                    AdminScorecardCard(scorecard: scorecard)
                }
            }
        }
    }
}

private struct AdminScorecardCard: View {
    let scorecard: AdminEvalScorecard

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(scorecard.name.adminDisplayLabel)
                        .font(.headline.weight(.bold))
                        .foregroundStyle(.white)
                        .lineLimit(2)

                    if let generatedAt = scorecard.generatedAt {
                        Text(generatedAt.adminGeneratedText)
                            .font(.caption)
                            .foregroundStyle(.white.opacity(0.58))
                    }
                }

                Spacer(minLength: 10)

                AdminStatusBadge(status: scorecard.status)
            }

            HStack(alignment: .firstTextBaseline, spacing: 8) {
                Text(scorecard.overallScore.adminScoreText)
                    .font(.system(size: 34, weight: .black, design: .rounded))
                    .foregroundStyle(.white)
                Text("score")
                    .font(.caption.weight(.bold))
                    .foregroundStyle(.white.opacity(0.58))
            }

            if !scorecard.metrics.isEmpty {
                VStack(spacing: 8) {
                    ForEach(Array(scorecard.sortedMetrics.prefix(4)), id: \.key) { metric in
                        HStack {
                            Text(metric.key.adminDisplayLabel)
                                .foregroundStyle(.white.opacity(0.68))
                            Spacer()
                            Text(metric.value.displayText)
                                .fontWeight(.semibold)
                                .foregroundStyle(.white)
                        }
                    }
                }
                .font(.caption)
            }

            if !scorecard.gates.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(Array(scorecard.sortedGates.prefix(4)), id: \.key) { gate in
                        Label(gate.key.adminDisplayLabel, systemImage: gate.value ? "checkmark.circle.fill" : "xmark.octagon.fill")
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(gate.value ? .green : .red)
                    }
                }
            }

            ForEach(scorecard.notes.prefix(2), id: \.self) { note in
                Text(note)
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.68))
                    .lineLimit(3)
            }
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.white.opacity(0.07), in: RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(scorecard.status.adminStatusColor.opacity(0.3))
        )
    }
}

private struct AdminReportsSection: View {
    @ObservedObject var viewModel: AdminViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            AdminSectionHeader(
                title: "Open reports",
                subtitle: "\(viewModel.openReports.count) waiting",
                systemImage: "flag"
            )

            if viewModel.openReports.isEmpty {
                AdminEmptyState(title: "No open reports", systemImage: "checkmark.shield")
            } else {
                ForEach(viewModel.openReports.prefix(8)) { report in
                    AdminReportRow(
                        report: report,
                        isActionedWorking: viewModel.isActionInFlight("report:\(report.id):actioned"),
                        isDismissWorking: viewModel.isActionInFlight("report:\(report.id):dismissed"),
                        onActioned: {
                            Task { await viewModel.resolveReport(report, status: "actioned") }
                        },
                        onDismiss: {
                            Task { await viewModel.resolveReport(report, status: "dismissed") }
                        }
                    )
                }
            }
        }
    }
}

private struct AdminReportRow: View {
    let report: AdminReport
    let isActionedWorking: Bool
    let isDismissWorking: Bool
    let onActioned: () -> Void
    let onDismiss: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: report.targetType == "comment" ? "bubble.left.fill" : "play.rectangle.fill")
                    .foregroundStyle(.orange)
                    .frame(width: 26, height: 26)

                VStack(alignment: .leading, spacing: 4) {
                    Text(report.reason.adminDisplayLabel)
                        .font(.subheadline.weight(.bold))
                        .foregroundStyle(.white)
                        .lineLimit(2)

                    Text("\(report.targetType.adminDisplayLabel) \(report.targetId.adminShortID)")
                        .font(.caption)
                        .foregroundStyle(.white.opacity(0.6))
                        .monospaced()
                }

                Spacer()

                AdminStatusBadge(status: report.status)
            }

            if let details = report.details, !details.isEmpty {
                Text(details)
                    .font(.footnote)
                    .foregroundStyle(.white.opacity(0.72))
                    .lineLimit(3)
            }

            HStack {
                Text(report.createdAt.adminRelativeText)
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.54))

                Spacer()

                AdminActionButton(
                    title: "Actioned",
                    systemImage: "checkmark.circle",
                    tint: .green,
                    isWorking: isActionedWorking,
                    action: onActioned
                )

                AdminActionButton(
                    title: "Dismiss",
                    systemImage: "xmark.circle",
                    tint: .gray,
                    isWorking: isDismissWorking,
                    action: onDismiss
                )
            }
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.white.opacity(0.06), in: RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(.white.opacity(0.1))
        )
    }
}

private struct AdminVideosSection: View {
    @ObservedObject var viewModel: AdminViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            AdminSectionHeader(
                title: "Pending videos",
                subtitle: "\(viewModel.pendingVideos.count) awaiting review",
                systemImage: "play.rectangle"
            )

            if viewModel.pendingVideos.isEmpty {
                AdminEmptyState(title: "No pending videos", systemImage: "checkmark.seal")
            } else {
                ForEach(viewModel.pendingVideos.prefix(8)) { video in
                    AdminVideoRow(
                        video: video,
                        approveWorking: viewModel.isActionInFlight("video:\(video.id):approved"),
                        hideWorking: viewModel.isActionInFlight("video:\(video.id):hidden"),
                        onApprove: {
                            Task { await viewModel.updateVideo(video, status: "approved") }
                        },
                        onHide: {
                            Task { await viewModel.updateVideo(video, status: "hidden") }
                        }
                    )
                }
            }
        }
    }
}

private struct AdminVideoRow: View {
    let video: FeedVideo
    let approveWorking: Bool
    let hideWorking: Bool
    let onApprove: () -> Void
    let onHide: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top, spacing: 12) {
                AsyncImage(url: video.thumbnailURL) { phase in
                    switch phase {
                    case let .success(image):
                        image
                            .resizable()
                            .scaledToFill()
                    default:
                        ZStack {
                            Color.white.opacity(0.08)
                            Image(systemName: "play.rectangle")
                                .foregroundStyle(.white.opacity(0.6))
                        }
                    }
                }
                .frame(width: 58, height: 82)
                .clipShape(RoundedRectangle(cornerRadius: 8))
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(.white.opacity(0.1))
                )

                VStack(alignment: .leading, spacing: 6) {
                    Text(video.title)
                        .font(.subheadline.weight(.bold))
                        .foregroundStyle(.white)
                        .lineLimit(3)

                    Text(video.creator?.feedName ?? "Unknown creator")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.white.opacity(0.64))

                    HStack(spacing: 8) {
                        AdminScoreChip(label: "Spirit", value: video.spiritualScore)
                        AdminScoreChip(label: "Theo", value: video.theologyScore)
                    }
                }

                Spacer()
            }

            HStack {
                Text("Pending")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.cyan)

                Spacer()

                AdminActionButton(
                    title: "Approve",
                    systemImage: "checkmark.circle",
                    tint: .green,
                    isWorking: approveWorking,
                    action: onApprove
                )

                AdminActionButton(
                    title: "Hide",
                    systemImage: "eye.slash",
                    tint: .red,
                    isWorking: hideWorking,
                    action: onHide
                )
            }
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.white.opacity(0.06), in: RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(.white.opacity(0.1))
        )
    }
}

private struct AdminCommentsSection: View {
    @ObservedObject var viewModel: AdminViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            AdminSectionHeader(
                title: "Pending comments",
                subtitle: "\(viewModel.pendingComments.count) awaiting review",
                systemImage: "bubble.left.and.bubble.right"
            )

            if viewModel.pendingComments.isEmpty {
                AdminEmptyState(title: "No pending comments", systemImage: "checkmark.message")
            } else {
                ForEach(viewModel.pendingComments.prefix(8)) { comment in
                    AdminCommentRow(
                        comment: comment,
                        showWorking: viewModel.isActionInFlight("comment:\(comment.id):visible"),
                        hideWorking: viewModel.isActionInFlight("comment:\(comment.id):hidden"),
                        onShow: {
                            Task { await viewModel.updateComment(comment, status: "visible") }
                        },
                        onHide: {
                            Task { await viewModel.updateComment(comment, status: "hidden") }
                        }
                    )
                }
            }
        }
    }
}

private struct AdminCommentRow: View {
    let comment: Comment
    let showWorking: Bool
    let hideWorking: Bool
    let onShow: () -> Void
    let onHide: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(comment.body)
                .font(.subheadline)
                .foregroundStyle(.white)
                .lineLimit(4)

            HStack(spacing: 8) {
                Label(comment.userID?.adminShortID ?? "Unknown", systemImage: "person.crop.circle")
                Label(comment.videoID.adminShortID, systemImage: "play.rectangle")
                Spacer()
                Text(comment.createdAt?.adminRelativeText ?? "New")
            }
            .font(.caption)
            .foregroundStyle(.white.opacity(0.58))

            HStack {
                AdminStatusBadge(status: comment.moderationStatus ?? "pending")

                Spacer()

                AdminActionButton(
                    title: "Show",
                    systemImage: "eye",
                    tint: .green,
                    isWorking: showWorking,
                    action: onShow
                )

                AdminActionButton(
                    title: "Hide",
                    systemImage: "eye.slash",
                    tint: .red,
                    isWorking: hideWorking,
                    action: onHide
                )
            }
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.white.opacity(0.06), in: RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(.white.opacity(0.1))
        )
    }
}

private struct AdminSectionHeader: View {
    let title: String
    let subtitle: String
    let systemImage: String

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: systemImage)
                .foregroundStyle(.white.opacity(0.78))
                .frame(width: 22)

            VStack(alignment: .leading, spacing: 3) {
                Text(title)
                    .font(.headline.weight(.bold))
                    .foregroundStyle(.white)
                Text(subtitle)
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.58))
            }

            Spacer()
        }
    }
}

private struct AdminStatusBadge: View {
    let status: String

    var body: some View {
        Text(status.adminDisplayLabel)
            .font(.caption2.weight(.black))
            .foregroundStyle(status.adminStatusColor)
            .padding(.horizontal, 8)
            .padding(.vertical, 5)
            .background(status.adminStatusColor.opacity(0.16), in: Capsule())
            .overlay(
                Capsule()
                    .stroke(status.adminStatusColor.opacity(0.25))
            )
    }
}

private struct AdminScoreChip: View {
    let label: String
    let value: Double?

    var body: some View {
        HStack(spacing: 4) {
            Text(label)
            Text((value ?? 0).adminScoreText)
                .fontWeight(.bold)
        }
        .font(.caption2)
        .foregroundStyle(.white.opacity(0.72))
        .padding(.horizontal, 7)
        .padding(.vertical, 4)
        .background(.white.opacity(0.08), in: Capsule())
    }
}

private struct AdminActionButton: View {
    let title: String
    let systemImage: String
    let tint: Color
    let isWorking: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 5) {
                if isWorking {
                    ProgressView()
                        .controlSize(.small)
                        .tint(tint)
                } else {
                    Image(systemName: systemImage)
                }
                Text(title)
            }
            .font(.caption.weight(.bold))
            .foregroundStyle(tint)
            .padding(.horizontal, 9)
            .padding(.vertical, 7)
            .background(tint.opacity(0.15), in: Capsule())
        }
        .buttonStyle(.plain)
        .disabled(isWorking)
    }
}

private struct AdminEmptyState: View {
    let title: String
    let systemImage: String

    var body: some View {
        Label(title, systemImage: systemImage)
            .font(.footnote.weight(.semibold))
            .foregroundStyle(.white.opacity(0.62))
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(14)
            .background(.white.opacity(0.04), in: RoundedRectangle(cornerRadius: 8))
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(.white.opacity(0.08))
            )
    }
}

@MainActor
final class AdminViewModel: ObservableObject {
    @Published private(set) var recommendationScorecard: AdminEvalScorecard?
    @Published private(set) var ingestRedTeamScorecard: AdminEvalScorecard?
    @Published private(set) var openReports: [AdminReport] = []
    @Published private(set) var pendingVideos: [FeedVideo] = []
    @Published private(set) var pendingComments: [Comment] = []
    @Published private(set) var isLoading = false
    @Published private(set) var errorMessage: String?
    @Published private(set) var statusMessage: String?
    @Published private(set) var lastLoadedAt: Date?

    private var apiClient: APIClient?
    @Published private var actionIDs: Set<String> = []

    var hasLoaded: Bool {
        lastLoadedAt != nil
    }

    var scorecards: [AdminEvalScorecard] {
        [recommendationScorecard, ingestRedTeamScorecard].compactMap { $0 }
    }

    func load(using apiClient: APIClient) async {
        guard !hasLoaded else { return }
        await reload(using: apiClient)
    }

    func reload(using apiClient: APIClient) async {
        self.apiClient = apiClient
        isLoading = true
        defer {
            isLoading = false
            lastLoadedAt = Date()
        }

        do {
            async let recommendation = apiClient.adminRecommendationEval(limit: 30)
            async let ingestRedTeam = apiClient.adminRedTeamIngestEval()
            async let reports = apiClient.adminReports(status: "open")
            async let videos = apiClient.adminVideos(moderationStatus: "pending")
            async let comments = apiClient.adminComments(moderationStatus: "pending")

            let loaded = try await (recommendation, ingestRedTeam, reports, videos, comments)
            recommendationScorecard = loaded.0
            ingestRedTeamScorecard = loaded.1
            openReports = loaded.2
            pendingVideos = loaded.3
            pendingComments = loaded.4
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func isActionInFlight(_ actionID: String) -> Bool {
        actionIDs.contains(actionID)
    }

    func resolveReport(_ report: AdminReport, status: String) async {
        await performAction(
            id: "report:\(report.id):\(status)",
            successMessage: "Report marked \(status.adminDisplayLabel.lowercased())."
        ) { apiClient in
            try await apiClient.resolveAdminReport(
                reportID: report.id,
                status: status,
                notes: "Reviewed from mobile admin"
            )
        }
    }

    func updateVideo(_ video: FeedVideo, status: String) async {
        await performAction(
            id: "video:\(video.id):\(status)",
            successMessage: "Video marked \(status.adminDisplayLabel.lowercased())."
        ) { apiClient in
            try await apiClient.moderateAdminVideo(
                videoID: video.id,
                status: status,
                notes: "Reviewed from mobile admin"
            )
        }
    }

    func updateComment(_ comment: Comment, status: String) async {
        await performAction(
            id: "comment:\(comment.id):\(status)",
            successMessage: "Comment marked \(status.adminDisplayLabel.lowercased())."
        ) { apiClient in
            try await apiClient.moderateAdminComment(
                commentID: comment.id,
                status: status,
                notes: "Reviewed from mobile admin"
            )
        }
    }

    private func performAction(
        id: String,
        successMessage: String,
        operation: (APIClient) async throws -> Void
    ) async {
        guard let apiClient, !actionIDs.contains(id) else { return }
        actionIDs.insert(id)
        defer { actionIDs.remove(id) }

        do {
            try await operation(apiClient)
            statusMessage = successMessage
            errorMessage = nil
            await reload(using: apiClient)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

private enum AdminDateFormatters {
    static let relative: RelativeDateTimeFormatter = {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .short
        return formatter
    }()

    static let isoWithFractionalSeconds: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter
    }()

    static let iso: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        return formatter
    }()
}

private extension AdminEvalScorecard {
    var sortedMetrics: [(key: String, value: AdminMetricValue)] {
        metrics.sorted { $0.key < $1.key }
    }

    var sortedGates: [(key: String, value: Bool)] {
        gates.sorted {
            if $0.value == $1.value {
                return $0.key < $1.key
            }
            return !$0.value && $1.value
        }
    }
}

private extension AdminMetricValue {
    var displayText: String {
        switch self {
        case let .bool(value):
            return value ? "Yes" : "No"
        case let .number(value):
            return value.adminScoreText
        case let .string(value):
            return value.adminDisplayLabel
        case .empty:
            return "-"
        }
    }
}

private extension Double {
    var adminScoreText: String {
        if abs(self.rounded() - self) < 0.0001 {
            return "\(Int(self.rounded()))"
        }
        return String(format: "%.2f", self)
    }
}

private extension Date {
    var adminRelativeText: String {
        AdminDateFormatters.relative.localizedString(for: self, relativeTo: Date())
    }
}

private extension String {
    var adminDisplayLabel: String {
        replacingOccurrences(of: "_", with: " ")
            .replacingOccurrences(of: "-", with: " ")
            .capitalized
    }

    var adminShortID: String {
        count > 10 ? "\(prefix(10))..." : self
    }

    var adminGeneratedText: String {
        let date = AdminDateFormatters.isoWithFractionalSeconds.date(from: self)
            ?? AdminDateFormatters.iso.date(from: self)
        return date.map { "Generated \($0.adminRelativeText)" } ?? "Generated recently"
    }

    var adminStatusColor: Color {
        switch lowercased() {
        case "healthy", "approved", "visible", "actioned", "active", "reinstated", "restore":
            return .green
        case "baseline", "open", "pending", "watch":
            return .orange
        case "hidden", "rejected", "regressed", "suspended":
            return .red
        case "dismissed":
            return .gray
        default:
            return .cyan
        }
    }
}

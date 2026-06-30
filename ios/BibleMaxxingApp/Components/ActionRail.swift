import SwiftUI

struct ActionRail: View {
    let isLiked: Bool
    let isSaved: Bool
    let isCreatorFollowed: Bool
    let onLike: () -> Void
    let onSave: () -> Void
    let onComment: () -> Void
    let onNotInterested: () -> Void
    let onReport: () -> Void
    let onBlock: () -> Void
    let onFollowCreator: () -> Void

    var body: some View {
        VStack(spacing: 18) {
            FeedIconButton(
                systemName: isLiked ? "heart.fill" : "heart",
                title: isLiked ? "Liked" : "Like",
                tint: isLiked ? .pink : .white,
                action: onLike
            )

            FeedIconButton(
                systemName: isSaved ? "bookmark.fill" : "bookmark",
                title: isSaved ? "Saved" : "Save",
                tint: isSaved ? .yellow : .white,
                action: onSave
            )

            FeedIconButton(systemName: "bubble.right", title: "Comment", tint: .white, action: onComment)
            FeedIconButton(systemName: "hand.thumbsdown", title: "Not for me", tint: .white, action: onNotInterested)
            FeedIconButton(systemName: isCreatorFollowed ? "checkmark.circle.fill" : "plus.circle", title: isCreatorFollowed ? "Following" : "Follow", tint: isCreatorFollowed ? .green : .white, action: onFollowCreator)

            Menu {
                Button(role: .destructive, action: onReport) {
                    Label("Report video", systemImage: "flag")
                }
                Button(role: .destructive, action: onBlock) {
                    Label("Block creator", systemImage: "nosign")
                }
            } label: {
                VStack(spacing: 5) {
                    Image(systemName: "ellipsis.circle")
                        .font(.system(size: 28, weight: .semibold))
                    Text("More")
                        .font(.caption2.weight(.semibold))
                }
                .foregroundStyle(.white)
                .frame(width: 62)
                .padding(.vertical, 4)
            }
            .accessibilityLabel("More moderation actions")
        }
        .shadow(color: .black.opacity(0.45), radius: 8)
    }
}

private struct FeedIconButton: View {
    let systemName: String
    let title: String
    let tint: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 5) {
                Image(systemName: systemName)
                    .font(.system(size: 28, weight: .semibold))
                    .symbolRenderingMode(.hierarchical)
                Text(title)
                    .font(.caption2.weight(.semibold))
                    .lineLimit(1)
                    .minimumScaleFactor(0.78)
            }
            .foregroundStyle(tint)
            .frame(width: 62)
            .padding(.vertical, 4)
        }
        .buttonStyle(.plain)
        .accessibilityLabel(title)
    }
}

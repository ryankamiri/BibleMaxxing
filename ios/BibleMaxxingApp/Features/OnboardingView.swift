import SwiftUI

struct OnboardingView: View {
    @EnvironmentObject private var session: SessionStore
    @State private var selectedTopicSlugs: Set<String> = []
    @State private var intensity: FeedIntensity = .balanced
    @State private var isSubmitting = false

    private let columns = [
        GridItem(.adaptive(minimum: 142), spacing: 10)
    ]

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()

            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Shape your feed")
                            .font(.largeTitle.weight(.black))
                        Text("Choose topics that will help you follow Christ with more attention and less compulsion.")
                            .font(.body)
                            .foregroundStyle(.secondary)
                    }
                    .padding(.top, 40)

                    LazyVGrid(columns: columns, alignment: .leading, spacing: 10) {
                        ForEach(BibleMaxxingTopics.onboarding) { topic in
                            TopicChip(
                                title: topic.name,
                                isSelected: selectedTopicSlugs.contains(topic.slug)
                            ) {
                                toggle(topic.slug)
                            }
                        }
                    }

                    VStack(alignment: .leading, spacing: 10) {
                        Text("Feed intensity")
                            .font(.headline)
                        Picker("Feed intensity", selection: $intensity) {
                            ForEach(FeedIntensity.allCases) { option in
                                Text(option.title).tag(option)
                            }
                        }
                        .pickerStyle(.segmented)
                    }

                    Button {
                        Task { await submit() }
                    } label: {
                        HStack {
                            if isSubmitting {
                                ProgressView()
                                    .tint(.black)
                            }
                            Text("Start feed")
                                .fontWeight(.bold)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 15)
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.white)
                    .foregroundStyle(.black)
                    .disabled(selectedTopicSlugs.isEmpty || isSubmitting)

                    if let error = session.errorMessage {
                        Text(error)
                            .font(.footnote.weight(.medium))
                            .foregroundStyle(.red)
                    }
                }
                .padding(24)
            }
        }
    }

    private func toggle(_ slug: String) {
        if selectedTopicSlugs.contains(slug) {
            selectedTopicSlugs.remove(slug)
        } else {
            selectedTopicSlugs.insert(slug)
        }
    }

    private func submit() async {
        isSubmitting = true
        defer { isSubmitting = false }
        await session.completeOnboarding(topicSlugs: Array(selectedTopicSlugs).sorted(), intensity: intensity.rawValue)
    }
}

private enum FeedIntensity: String, CaseIterable, Identifiable {
    case gentle
    case balanced
    case focused

    var id: String { rawValue }

    var title: String {
        switch self {
        case .gentle:
            return "Gentle"
        case .balanced:
            return "Balanced"
        case .focused:
            return "Focused"
        }
    }
}

private struct TopicChip: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                Text(title)
                    .lineLimit(2)
                    .multilineTextAlignment(.center)
                    .minimumScaleFactor(0.86)
            }
            .font(.subheadline.weight(.semibold))
            .frame(maxWidth: .infinity, minHeight: 52)
            .padding(.horizontal, 12)
            .background(isSelected ? Color.white : Color.white.opacity(0.08), in: RoundedRectangle(cornerRadius: 8))
            .foregroundStyle(isSelected ? Color.black : Color.white)
        }
        .buttonStyle(.plain)
        .accessibilityLabel(title)
        .accessibilityAddTraits(isSelected ? .isSelected : [])
    }
}

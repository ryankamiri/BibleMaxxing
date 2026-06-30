import SwiftUI

struct RootView: View {
    @EnvironmentObject private var session: SessionStore

    var body: some View {
        Group {
            if session.isCheckingSession {
                LaunchLoadingView()
            } else if !session.isAuthenticated {
                AuthView()
            } else if session.requiresOnboarding {
                OnboardingView()
            } else {
                FeedView()
            }
        }
        .background(Color.black)
        .task {
            await session.refreshFromStoredToken()
        }
    }
}

private struct LaunchLoadingView: View {
    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            VStack(spacing: 18) {
                Text("BibleMaxxing")
                    .font(.system(size: 34, weight: .black, design: .rounded))
                Text("Don't brainrot. BibleMax.")
                    .font(.headline)
                    .foregroundStyle(.secondary)
                ProgressView()
                    .tint(.white)
                    .padding(.top, 8)
            }
        }
    }
}

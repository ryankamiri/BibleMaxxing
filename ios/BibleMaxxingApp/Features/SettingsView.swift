import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var session: SessionStore
    @Environment(\.dismiss) private var dismiss

    @State private var showDeleteConfirmation = false
    @State private var isDeleting = false

    var body: some View {
        NavigationStack {
            Form {
                if let user = session.currentUser {
                    Section("Account") {
                        LabeledContent("Username", value: user.username)
                        LabeledContent("Email", value: user.email)
                        LabeledContent("Profile", value: "Public")
                    }
                }

                Section("Playback and safety") {
                    Label("Videos play from YouTube with source attribution.", systemImage: "play.rectangle")
                    Label("Saves stay inside BibleMaxxing.", systemImage: "bookmark")
                    Label("Reports and blocks help keep the feed safe.", systemImage: "shield")
                }

                Section("Legal and support") {
                    ForEach(PublicPage.allCases) { page in
                        Link(destination: session.apiClient.publicPageURL(page)) {
                            Label(page.title, systemImage: page.systemImage)
                        }
                    }
                }

                if session.currentUser?.isAdmin == true {
                    Section("Admin") {
                        NavigationLink {
                            AdminView()
                                .environmentObject(session)
                        } label: {
                            Label("Admin dashboard", systemImage: "shield.lefthalf.filled")
                        }
                    }
                }

                Section {
                    Button {
                        Task {
                            await session.logout()
                            dismiss()
                        }
                    } label: {
                        Label("Log out", systemImage: "rectangle.portrait.and.arrow.right")
                    }

                    Button(role: .destructive) {
                        showDeleteConfirmation = true
                    } label: {
                        if isDeleting {
                            ProgressView()
                        } else {
                            Label("Delete account", systemImage: "trash")
                        }
                    }
                    .disabled(isDeleting)
                }

                if let error = session.errorMessage {
                    Section("Status") {
                        Text(error)
                            .foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") { dismiss() }
                }
            }
            .confirmationDialog(
                "Delete this BibleMaxxing account?",
                isPresented: $showDeleteConfirmation,
                titleVisibility: .visible
            ) {
                Button("Delete account", role: .destructive) {
                    Task {
                        isDeleting = true
                        await session.deleteAccount()
                        isDeleting = false
                        dismiss()
                    }
                }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("This permanently deletes your account and signs you out on this device.")
            }
        }
        .preferredColorScheme(.dark)
    }
}

private extension PublicPage {
    var systemImage: String {
        switch self {
        case .privacy:
            return "lock.shield"
        case .terms:
            return "doc.text"
        case .community:
            return "person.2"
        case .support:
            return "envelope"
        }
    }
}

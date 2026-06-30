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

                Section("Feed posture") {
                    Label("YouTube videos play through the official embedded player.", systemImage: "play.rectangle")
                    Label("Saves are in-app bookmarks only.", systemImage: "bookmark")
                    Label("Reports and blocks are sent to moderation endpoints.", systemImage: "shield")
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
                Text("This calls the backend account deletion endpoint and removes the local session token.")
            }
        }
        .preferredColorScheme(.dark)
    }
}

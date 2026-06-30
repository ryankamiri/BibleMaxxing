import AuthenticationServices
import SwiftUI

struct AuthView: View {
    @EnvironmentObject private var session: SessionStore

    @State private var mode: AuthMode = .login
    @State private var username = ""
    @State private var email = ""
    @State private var password = ""
    @State private var birthday = Calendar.current.date(byAdding: .year, value: -18, to: Date()) ?? Date()
    @State private var isWorking = false

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()

            ScrollView {
                VStack(alignment: .leading, spacing: 22) {
                    HStack(alignment: .center, spacing: 14) {
                        BrandLogoView(size: 58)

                        VStack(alignment: .leading, spacing: 5) {
                            Text("BibleMaxxing")
                                .font(.system(size: 36, weight: .black, design: .rounded))
                            Text("Don't brainrot. BibleMax.")
                                .font(.headline.weight(.semibold))
                                .foregroundStyle(.secondary)
                        }
                    }
                    .padding(.top, 34)

                    VStack(spacing: 13) {
                        Picker("Mode", selection: $mode) {
                            ForEach(AuthMode.allCases) { mode in
                                Text(mode.title).tag(mode)
                            }
                        }
                        .pickerStyle(.segmented)

                        if mode == .register {
                            AuthField(title: "Username", text: $username, contentType: .username)

                            DatePicker(
                                "Birthday",
                                selection: $birthday,
                                in: ...Self.latestAllowedBirthday,
                                displayedComponents: .date
                            )
                            .datePickerStyle(.compact)
                            .padding(13)
                            .background(.white.opacity(0.08), in: RoundedRectangle(cornerRadius: 8))
                            .accessibilityLabel("Birthday")

                            HStack(spacing: 6) {
                                Image(systemName: "checkmark.shield")
                                Text("Ages 13 and up")
                            }
                            .font(.footnote.weight(.semibold))
                            .foregroundStyle(.secondary)
                            .padding(.horizontal, 2)

                        }

                        AuthField(title: "Email", text: $email, keyboard: .emailAddress, contentType: .emailAddress)

                        SecureField("Password", text: $password)
                            .textContentType(mode == .login ? .password : .newPassword)
                            .padding(14)
                            .background(.white.opacity(0.08), in: RoundedRectangle(cornerRadius: 8))

                        Button {
                            Task { await submit() }
                        } label: {
                            HStack {
                                if isWorking {
                                    ProgressView()
                                        .tint(.black)
                                }
                                Text(mode.cta)
                                    .fontWeight(.bold)
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 14)
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.white)
                        .foregroundStyle(.black)
                        .disabled(isWorking || email.isEmpty || password.isEmpty || (mode == .register && username.isEmpty))

                        SignInWithAppleButton(.signIn, onRequest: configureAppleRequest, onCompletion: handleAppleCompletion)
                            .signInWithAppleButtonStyle(.whiteOutline)
                            .frame(height: 46)
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                    .padding(16)
                    .background(.white.opacity(0.06), in: RoundedRectangle(cornerRadius: 8))

                    VStack(alignment: .leading, spacing: 8) {
                        Text("Ages 13 and up.")
                            .font(.footnote.weight(.semibold))
                        Text("We use your email to secure your account. Phone numbers are never collected.")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }

                    if let error = session.errorMessage {
                        Text(error)
                            .font(.footnote.weight(.medium))
                            .foregroundStyle(.red)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                .padding(.horizontal, 24)
                .padding(.bottom, 96)
            }
            .scrollDismissesKeyboard(.interactively)
        }
    }

    private func submit() async {
        isWorking = true
        defer { isWorking = false }

        switch mode {
        case .login:
            await session.login(email: email, password: password)
        case .register:
            guard birthday <= Self.latestAllowedBirthday else {
                session.errorMessage = "BibleMaxxing requires users to be at least 13."
                return
            }
            await session.register(username: username, email: email, password: password, birthday: Self.birthdayFormatter.string(from: birthday))
        }
    }

    private func configureAppleRequest(_ request: ASAuthorizationAppleIDRequest) {
        request.requestedScopes = [.email, .fullName]
    }

    private func handleAppleCompletion(_ result: Result<ASAuthorization, Error>) {
        switch result {
        case let .success(authorization):
            guard let credential = authorization.credential as? ASAuthorizationAppleIDCredential else {
                session.errorMessage = "Apple did not return an identity credential."
                return
            }
            let identityToken = credential.identityToken.flatMap { String(data: $0, encoding: .utf8) }
            let authorizationCode = credential.authorizationCode.flatMap { String(data: $0, encoding: .utf8) }
            Task {
                await session.signInWithApple(identityToken: identityToken, authorizationCode: authorizationCode)
            }
        case let .failure(error):
            session.errorMessage = error.localizedDescription
        }
    }

    private static var latestAllowedBirthday: Date {
        Calendar.current.date(byAdding: .year, value: -13, to: Date()) ?? Date()
    }

    private static let birthdayFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()
}

private struct AuthField: View {
    let title: String
    @Binding var text: String
    var keyboard: UIKeyboardType = .default
    var contentType: UITextContentType?

    var body: some View {
        TextField(title, text: $text)
            .keyboardType(keyboard)
            .textContentType(contentType)
            .textInputAutocapitalization(.never)
            .autocorrectionDisabled()
            .padding(13)
            .background(.white.opacity(0.08), in: RoundedRectangle(cornerRadius: 8))
    }
}

private enum AuthMode: String, CaseIterable, Identifiable {
    case login
    case register

    var id: String { rawValue }

    var title: String {
        switch self {
        case .login:
            return "Log in"
        case .register:
            return "Create account"
        }
    }

    var cta: String {
        switch self {
        case .login:
            return "Log in"
        case .register:
            return "Create account"
        }
    }
}

import Foundation
import Security

@MainActor
final class SessionStore: ObservableObject {
    @Published private(set) var currentUser: User?
    @Published private(set) var isCheckingSession = true
    @Published var errorMessage: String?

    let apiClient: APIClient
    private let tokenStore: TokenStoring

    var isAuthenticated: Bool {
        currentUser != nil
    }

    var requiresOnboarding: Bool {
        !(currentUser?.onboardingCompleted ?? false)
    }

    init(apiClient: APIClient = .production, tokenStore: TokenStoring = KeychainTokenStore()) {
        self.apiClient = apiClient
        self.tokenStore = tokenStore
    }

    func refreshFromStoredToken() async {
        guard isCheckingSession else { return }
        defer { isCheckingSession = false }

        guard let token = tokenStore.loadToken() else {
            apiClient.bearerToken = nil
            return
        }

        apiClient.bearerToken = token
        do {
            currentUser = try await apiClient.currentUser()
        } catch {
            clearSession()
        }
    }

    func login(email: String, password: String) async {
        await performAuth {
            try await apiClient.login(email: email, password: password)
        }
    }

    func register(username: String, email: String, password: String, birthday: String?) async {
        await performAuth {
            try await apiClient.register(username: username, email: email, password: password, birthday: birthday)
        }
    }

    func signInWithApple(identityToken: String?, authorizationCode: String?) async {
        await performAuth {
            try await apiClient.signInWithApple(identityToken: identityToken, authorizationCode: authorizationCode)
        }
    }

    func completeOnboarding(topicSlugs: [String], intensity: String) async {
        guard !topicSlugs.isEmpty else {
            errorMessage = "Choose at least one topic to shape the feed."
            return
        }

        do {
            currentUser = try await apiClient.submitOnboarding(topics: topicSlugs, intensity: intensity)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func logout() async {
        clearSession()
    }

    func deleteAccount() async {
        do {
            try await apiClient.deleteAccount()
            clearSession()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func performAuth(_ operation: () async throws -> AuthResponse) async {
        do {
            let response = try await operation()
            tokenStore.saveToken(response.accessToken)
            apiClient.bearerToken = response.accessToken
            currentUser = response.user
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func clearSession() {
        tokenStore.deleteToken()
        apiClient.bearerToken = nil
        currentUser = nil
    }
}

protocol TokenStoring {
    func loadToken() -> String?
    func saveToken(_ token: String)
    func deleteToken()
}

struct KeychainTokenStore: TokenStoring {
    private let service = "org.tailortom.biblemaxxing.auth"
    private let account = "accessToken"

    func loadToken() -> String? {
        var query = baseQuery
        query[kSecReturnData as String] = true
        query[kSecMatchLimit as String] = kSecMatchLimitOne

        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        guard status == errSecSuccess, let data = item as? Data else {
            return nil
        }
        return String(data: data, encoding: .utf8)
    }

    func saveToken(_ token: String) {
        deleteToken()
        var item = baseQuery
        item[kSecValueData as String] = Data(token.utf8)
        SecItemAdd(item as CFDictionary, nil)
    }

    func deleteToken() {
        SecItemDelete(baseQuery as CFDictionary)
    }

    private var baseQuery: [String: Any] {
        [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        ]
    }
}

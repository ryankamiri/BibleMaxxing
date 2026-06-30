import OSLog
import SwiftUI
import WebKit

struct YouTubePlayerView: UIViewRepresentable {
    let videoID: String
    let playerURL: URL
    let isActive: Bool
    let shouldAutoplay: Bool

    func makeCoordinator() -> Coordinator {
        Coordinator(videoID: videoID)
    }

    func makeUIView(context: Context) -> WKWebView {
        let contentController = WKUserContentController()
        contentController.add(context.coordinator, name: Coordinator.messageHandlerName)

        let configuration = WKWebViewConfiguration()
        configuration.allowsInlineMediaPlayback = true
        configuration.defaultWebpagePreferences.allowsContentJavaScript = true
        configuration.mediaTypesRequiringUserActionForPlayback = []
        configuration.userContentController = contentController

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.isOpaque = false
        webView.backgroundColor = .black
        webView.navigationDelegate = context.coordinator
        webView.scrollView.isScrollEnabled = false
        webView.scrollView.backgroundColor = .black
        load(playerURL, videoID: videoID, into: webView, context: context)
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        context.coordinator.videoID = videoID

        if context.coordinator.loadedVideoID != videoID {
            load(playerURL, videoID: videoID, into: webView, context: context)
        }

        context.coordinator.setDesiredPlayback(isActive && shouldAutoplay, in: webView)
    }

    static func dismantleUIView(_ uiView: WKWebView, coordinator: Coordinator) {
        uiView.stopLoading()
        uiView.navigationDelegate = nil
        uiView.configuration.userContentController.removeScriptMessageHandler(
            forName: Coordinator.messageHandlerName
        )
    }

    private func load(
        _ playerURL: URL,
        videoID: String,
        into webView: WKWebView,
        context: Context
    ) {
        var request = URLRequest(
            url: playerURL,
            cachePolicy: .reloadIgnoringLocalCacheData,
            timeoutInterval: 20
        )
        request.setValue("text/html,application/xhtml+xml", forHTTPHeaderField: "Accept")
        context.coordinator.loadedVideoID = videoID
        webView.load(request)
    }

    final class Coordinator: NSObject, WKNavigationDelegate, WKScriptMessageHandler {
        static let messageHandlerName = "bibleMaxxingPlayer"

        var videoID: String
        var loadedVideoID: String?
        private var desiredPlayback = false
        private let logger = Logger(subsystem: "BibleMaxxing", category: "YouTubePlayer")

        init(videoID: String) {
            self.videoID = videoID
        }

        func setDesiredPlayback(_ shouldPlay: Bool, in webView: WKWebView) {
            guard desiredPlayback != shouldPlay else { return }
            desiredPlayback = shouldPlay
            evaluatePlaybackCommand(shouldPlay ? "playVideo()" : "pauseVideo()", in: webView)
        }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            logger.debug("YouTube player page loaded for \(self.videoID, privacy: .public)")
            if desiredPlayback {
                evaluatePlaybackCommand("playVideo()", in: webView)
            }
        }

        func webView(
            _ webView: WKWebView,
            didFail navigation: WKNavigation!,
            withError error: Error
        ) {
            logger.error(
                "YouTube player navigation failed for \(self.videoID, privacy: .public): \(error.localizedDescription, privacy: .public)"
            )
        }

        func webView(
            _ webView: WKWebView,
            didFailProvisionalNavigation navigation: WKNavigation!,
            withError error: Error
        ) {
            logger.error(
                "YouTube player provisional navigation failed for \(self.videoID, privacy: .public): \(error.localizedDescription, privacy: .public)"
            )
        }

        func userContentController(
            _ userContentController: WKUserContentController,
            didReceive message: WKScriptMessage
        ) {
            let body = String(describing: message.body)
            if let payload = message.body as? [String: Any],
               let type = payload["type"] as? String,
               ["player_error", "unavailable", "window_error"].contains(type) {
                logger.error("YouTube player JS message: \(body, privacy: .public)")
            } else {
                logger.info("YouTube player JS message: \(body, privacy: .public)")
            }
        }

        private func evaluatePlaybackCommand(_ command: String, in webView: WKWebView) {
            webView.evaluateJavaScript(command) { [logger, videoID] _, error in
                if let error {
                    logger.debug(
                        "YouTube player command \(command, privacy: .public) for \(videoID, privacy: .public) was not ready: \(error.localizedDescription, privacy: .public)"
                    )
                }
            }
        }
    }
}

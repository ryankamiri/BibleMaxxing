import SwiftUI
import WebKit

struct YouTubePlayerView: UIViewRepresentable {
    let videoID: String
    let isActive: Bool
    let shouldAutoplay: Bool

    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.allowsInlineMediaPlayback = true
        configuration.mediaTypesRequiringUserActionForPlayback = []

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.isOpaque = false
        webView.backgroundColor = .black
        webView.scrollView.isScrollEnabled = false
        webView.scrollView.backgroundColor = .black
        load(videoID: videoID, into: webView)
        context.coordinator.loadedVideoID = videoID
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        if context.coordinator.loadedVideoID != videoID {
            load(videoID: videoID, into: webView)
            context.coordinator.loadedVideoID = videoID
        }

        let command = isActive && shouldAutoplay ? "playVideo()" : "pauseVideo()"
        webView.evaluateJavaScript(command)
    }

    private func load(videoID: String, into webView: WKWebView) {
        webView.loadHTMLString(html(videoID: videoID, autoplay: shouldAutoplay), baseURL: URL(string: "https://www.youtube.com"))
    }

    private func html(videoID: String, autoplay: Bool) -> String {
        let escapedVideoID = videoID.jsEscaped
        let autoplayValue = autoplay ? 1 : 0

        return #"""
        <!doctype html>
        <html>
        <head>
          <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
          <style>
            html, body, #player {
              background: #000;
              height: 100%;
              margin: 0;
              overflow: hidden;
              width: 100%;
            }
          </style>
        </head>
        <body>
          <div id="player"></div>
          <script src="https://www.youtube.com/iframe_api"></script>
          <script>
            var player;
            function onYouTubeIframeAPIReady() {
              player = new YT.Player('player', {
                height: '100%',
                width: '100%',
                videoId: '\#(escapedVideoID)',
                playerVars: {
                  autoplay: \#(autoplayValue),
                  controls: 1,
                  enablejsapi: 1,
                  fs: 0,
                  modestbranding: 1,
                  playsinline: 1,
                  rel: 0
                },
                events: {
                  'onReady': function(event) {
                    if (\#(autoplayValue) === 1) {
                      event.target.unMute();
                      event.target.playVideo();
                    }
                  }
                }
              });
            }

            function playVideo() {
              if (player && player.playVideo) {
                player.unMute();
                player.playVideo();
              }
            }

            function pauseVideo() {
              if (player && player.pauseVideo) {
                player.pauseVideo();
              }
            }
          </script>
        </body>
        </html>
        """#
    }

    final class Coordinator {
        var loadedVideoID: String?
    }
}

private extension String {
    var jsEscaped: String {
        replacingOccurrences(of: "\\", with: "\\\\")
            .replacingOccurrences(of: "'", with: "\\'")
            .replacingOccurrences(of: "\n", with: "\\n")
            .replacingOccurrences(of: "\r", with: "")
    }
}

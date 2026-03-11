package dev.yuho;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * Java client for the Yuho legal DSL API.
 */
public class YuhoClient {
    private final String baseUrl;
    private final String authToken;
    private final HttpClient client;

    public YuhoClient(String baseUrl) {
        this(baseUrl, null);
    }

    public YuhoClient(String baseUrl, String authToken) {
        this.baseUrl = baseUrl.replaceAll("/$", "");
        this.authToken = authToken;
        this.client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(30))
                .build();
    }

    private HttpRequest.Builder requestBuilder(String path) {
        var builder = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + "/v1" + path))
                .header("Content-Type", "application/json")
                .timeout(Duration.ofSeconds(30));
        if (authToken != null && !authToken.isEmpty()) {
            builder.header("Authorization", "Bearer " + authToken);
        }
        return builder;
    }

    public String health() throws IOException, InterruptedException {
        var req = requestBuilder("/health").GET().build();
        return client.send(req, HttpResponse.BodyHandlers.ofString()).body();
    }

    public String parse(String source) throws IOException, InterruptedException {
        var body = String.format("{\"source\":%s}", jsonEscape(source));
        var req = requestBuilder("/parse")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();
        return client.send(req, HttpResponse.BodyHandlers.ofString()).body();
    }

    public String validate(String source) throws IOException, InterruptedException {
        var body = String.format("{\"source\":%s}", jsonEscape(source));
        var req = requestBuilder("/validate")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();
        return client.send(req, HttpResponse.BodyHandlers.ofString()).body();
    }

    public String transpile(String source, String target) throws IOException, InterruptedException {
        var body = String.format("{\"source\":%s,\"target\":\"%s\"}", jsonEscape(source), target);
        var req = requestBuilder("/transpile")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();
        return client.send(req, HttpResponse.BodyHandlers.ofString()).body();
    }

    private static String jsonEscape(String s) {
        return "\"" + s.replace("\\", "\\\\")
                       .replace("\"", "\\\"")
                       .replace("\n", "\\n")
                       .replace("\r", "\\r")
                       .replace("\t", "\\t") + "\"";
    }
}

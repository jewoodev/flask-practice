import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.*;
import java.net.http.*;
import java.util.*;
import java.nio.charset.StandardCharsets;

public class UpsJava {
    public static void main(String[] args) throws Exception {
        String accessToken = getAccessToken();
        var response = callUpsTrackingApi(accessToken, "1ZY8714C0319756518");

        System.out.println(response);
    }

    private static JsonNode callUpsTrackingApi(String accessToken, String inquiryNumber) {
        try {
            String queryParams = "?locale=en_US&returnSignature=false&returnMilestones=false&returnPOD=false";
            String url = String.format(
                    "https://onlinetools.ups.com/api/track/v1/details/%s%s",
                    inquiryNumber,
                    queryParams
            );

            HttpClient client = HttpClient.newHttpClient();

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .header("Authorization", "Bearer " + accessToken)
                    .header("Content-Type", "application/json")
                    .header("transId", UUID.randomUUID().toString())
                    .header("transactionSrc", "testing")
                    .GET()
                    .build();

            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

            // 응답 상태 확인
            if (response.statusCode() != 200) {
                System.out.println("Error from UPS Tracking API: " + response.body());
                return null;
            }

            ObjectMapper objectMapper = new ObjectMapper();
            return objectMapper.readTree(response.body());

        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    private static String getAccessToken() {
        String clientId = "my";
        String clientSecret = "my";

        // Base64 인코딩
        String credentials = Base64.getEncoder()
                .encodeToString((clientId + ":" + clientSecret).getBytes(StandardCharsets.UTF_8));

        try {
            // HTTP 클라이언트 생성
            HttpClient client = HttpClient.newHttpClient();

            // 요청 본문 데이터
            String requestBody = "grant_type=client_credentials";

            // HTTP 요청 생성
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create("https://onlinetools.ups.com/security/v1/oauth/token"))
                    .header("Content-Type", "application/x-www-form-urlencoded")
                    .header("Authorization", "Basic " + credentials)
                    .POST(HttpRequest.BodyPublishers.ofString(requestBody))
                    .build();

            // 요청 전송 및 응답 받기
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

            // 응답 상태 코드 확인
            if (response.statusCode() != 200) {
                System.out.println("Error from UPS Auth: " + response.body());
                return null;
            }

            // JSON 파싱
            ObjectMapper objectMapper = new ObjectMapper();
            JsonNode jsonNode = objectMapper.readTree(response.body());
            String accessToken = jsonNode.get("access_token").asText();

            return accessToken;

        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }
}

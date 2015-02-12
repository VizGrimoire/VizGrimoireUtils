package sample;

import org.sonar.wsclient.Host;
import org.sonar.wsclient.Sonar;
import org.sonar.wsclient.connectors.HttpClient4Connector;
import org.sonar.wsclient.services.*;
import java.util.List;
import java.io.BufferedReader;
import java.nio.charset.Charset;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.net.URL;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.LinkedHashMap;
import java.util.Map;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;
import org.json.simple.parser.ContainerFactory;

// http://stackoverflow.com/a/4308662
class JsonReader {
	private static String readAll(Reader rd) throws IOException {
		StringBuilder sb = new StringBuilder();
		int cp;
		while ((cp = rd.read()) != -1) {
			sb.append((char) cp);
		}
		return sb.toString();
	}

	public static List readJsonFromUrl(String url) throws IOException,
			ParseException {

		ContainerFactory containerFactory = new ContainerFactory() {
			public List creatArrayContainer() {
				return new LinkedList();
			}

			public Map createObjectContainer() {
				return new LinkedHashMap();
			}
		};

		InputStream is = new URL(url).openStream();
		try {
			BufferedReader rd = new BufferedReader(new InputStreamReader(is,
					Charset.forName("UTF-8")));
			String jsonText = readAll(rd);
			JSONParser parser = new JSONParser();
			List json = null;

			try {
				json = (List) parser.parse(jsonText, containerFactory);
				// json = parser.parse(jsonText);
			} catch (ParseException pe) {
				System.out.println("position: " + pe.getPosition());
				System.out.println(pe);
			}

			return json;
		} finally {
			is.close();
		}
	}
}

public class Polarsys {

	public static void getMetrics(Sonar sonar, String projectKey) {
		System.out.println("Getting metrics for " + projectKey);

		// dit metrics is not available in SONAR CDT project
		ResourceQuery query = ResourceQuery.createForMetrics(projectKey,
				"line_coverage", "tests", "test_success_density", "ncloc",
				"functions", "complexity", "comment_lines_density",
				"uncovered_lines", "duplicated_lines", "duplicated_lines_density", "weighted_violations",
				"public_api", "dit","branch_coverage","test_success_density","function_complexity");
		// query.setIncludeTrends(true);
		Resource metrics = sonar.find(query);

		JSONObject obj = new JSONObject();

		// getVariation2 for "7 days"
		// Metric tst_vol_idx = tests / (ncloc /1000)
		Double tests = null;
		Double ncloc = null;
		List<Measure> allMeasures = metrics.getMeasures();
		for (Measure measure : allMeasures) {
			System.out.println(measure.getMetricKey() + ": "
					+ measure.getValue());
			obj.put(measure.getMetricKey(), measure.getValue());
			if (measure.getMetricKey().equals("tests")) {
				tests = measure.getValue();
			}
			if (measure.getMetricKey().equals("ncloc")) {
				ncloc = measure.getValue();
			}
		}
		// Metric tst_vol_idx = tests / (ncloc /1000)
		obj.put("tst_vol_idx", tests / (ncloc /1000));
		System.out.println("tst_vol_idx" + ": " + tests / (ncloc /1000));


		try {
			FileWriter file = new FileWriter(projectKey + ".json");
			file.write(obj.toJSONString());
			file.flush();
			file.close();

		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	public static void main(String args[]) throws Exception {
		String url = "https://dev.eclipse.org/sonar";
		String login = "admin";
		String password = "admin";

		Sonar sonar = new Sonar(new HttpClient4Connector(new Host(url, login,
				password)));

		// Get projects list
		List json = JsonReader.readJsonFromUrl(url + "/api/resources");

		for (Object obj : json) {
			Map map = (LinkedHashMap) obj;
			System.out.println(map.get("key"));
			Polarsys.getMetrics(sonar, (String) map.get("key"));
		}
	}
}

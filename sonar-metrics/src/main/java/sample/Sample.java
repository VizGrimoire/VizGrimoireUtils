package sample;

import org.sonar.wsclient.Host;
import org.sonar.wsclient.Sonar;
import org.sonar.wsclient.connectors.HttpClient4Connector;
import org.sonar.wsclient.services.*;
import java.util.List;
import java.io.FileWriter;
import java.io.IOException;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;


public class Sample {

  public static void main(String args[]) {
    // Use Eclipse SONAR: https://dev.eclipse.org/sonar/api/metrics?resource=org.eclipse.mylyn.tasks:org.eclipse.mylyn.tasks-parent
    String url = "https://dev.eclipse.org/sonar";
    String login = "admin";
    String password = "admin";
    Sonar sonar = new Sonar(new HttpClient4Connector(new Host(url, login, password)));

    String projectKey = "org.eclipse.mylyn.tasks:org.eclipse.mylyn.tasks-parent";
    // String manualMetricKey = "burned_budget";
    String metricKey = "open_issues";

    // ResourceQuery query = ResourceQuery.createForMetrics(projectKey, "complexity","open_issues", "coverage", "lines", "violations");
    ResourceQuery query = ResourceQuery.createForMetrics(projectKey, "complexity","coverage");
    // query.setIncludeTrends(true);
    Resource mylyn = sonar.find(query);
    // mylyn.getMeasure("open_issues");

    JSONObject obj = new JSONObject();

    //getVariation2 for "7 days"
    List<Measure> allMeasures = mylyn.getMeasures();
    for (Measure measure : allMeasures) {
        System.out.println(measure.getMetricKey()+": "+measure.getValue());
    	obj.put(measure.getMetricKey(), measure.getValue());
    }

    try {
		FileWriter file = new FileWriter("eclipse_sonar.json");
		file.write(obj.toJSONString());
		file.flush();
		file.close();
 
	} catch (IOException e) {
		e.printStackTrace();
	}
 
	System.out.print(obj);
  }

}

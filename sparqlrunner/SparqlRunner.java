/* SparqlRunner
 * 
 * Simple java script to read RDF, process a number of UPDATE statements, and output the result
 * Input will be run from standard in and should be a json file containing 'data' and 'updates' keys 
 * Data and output are in N3/triples format
 * 
 * (C) Wouter van Atteveldt, Licensed under Apache License 2.0
 */

import java.io.*;
import com.hp.hpl.jena.query.* ;
import com.hp.hpl.jena.rdf.model.*;
import com.hp.hpl.jena.update.*;
import javax.json.*;

public class SparqlRunner {
    
    private BufferedReader input;
    private Model model;
    private boolean done = false;
    
    public SparqlRunner() {
	input = new BufferedReader(new InputStreamReader(System.in));
	model =  ModelFactory.createDefaultModel();
    }
	

    String readJson() throws Exception {
	StringBuilder buffer = new StringBuilder();
	while (true) {
	    String line = input.readLine();
	    if (line == null) done = true;
	    if (line == null || line.equals(""))
		return buffer.toString();
	    buffer.append(line);
	}
    }

    void handle(String jsonstr) throws Exception  {
	long t_start = System.currentTimeMillis();

	JsonObject json = (JsonObject) Json.createReader(new StringReader(jsonstr)).read();
	long t_decoded = System.currentTimeMillis();

	model.removeAll();
	long t_cleared = System.currentTimeMillis();
        model.read(new StringReader(json.getString("data")), null, "N3") ;
	long t_loaded = System.currentTimeMillis();

	// Perform updates
	UpdateRequest request = UpdateFactory.create() ;
	for (JsonValue val : (JsonArray) json.getJsonArray("updates")) {
	    System.err.println("SparqlRunner: Performing update");
	    String query = ((JsonString) val).getString();
	    try {
		request.add(query);
	    } catch(Exception e) {
		System.err.println("SparqlRunner: ERROR on executing query: "+e+"\n---\n"+query+"\n---");
		throw e;
	    }
	    
	}
	long t_requested = System.currentTimeMillis();
	UpdateAction.execute(request, model) ;
	long t_executed = System.currentTimeMillis();
	
	// Output results
	System.err.println("SparqlRunner: Writing model to STDOUT");
	model.write(System.out, "NT");

	long t_done = System.currentTimeMillis();

	System.err.println("Decoding: "+(t_decoded - t_start));
	System.err.println("Cleared model: "+(t_cleared - t_decoded));
	System.err.println("Loaded model: "+(t_loaded - t_cleared));
	System.err.println("Creating request: "+(t_requested - t_loaded));
	System.err.println("Executing request: "+(t_executed - t_requested));
	System.err.println("Writing output: "+(t_done - t_executed));
       
	System.err.println("SparqlRunner: DONE");
	System.err.println("SparqlRunner: READY");
	System.out.println();
    }

    void go() throws Exception {
	System.err.println("SparqlRunner: READY");
	System.out.println();
	while (!done) {
	    String json = readJson();
	    if (json != null && json.length() > 0)
		handle(json);
	}
	System.err.println("SparqlRunner: EOF -> DONE!");

    }

    public static void main(String[] args) throws Exception {
	new SparqlRunner().go();
    }
}

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
    public static void main(String[] args) throws Exception{
	JsonReader reader = Json.createReader(new InputStreamReader(System.in));
	JsonObject json = (JsonObject) reader.read();
	System.err.println("SparqlRunner: Reading model from STDIN");
	// Read data
	Model m = ModelFactory.createDefaultModel() ;
        m.read(new StringReader(json.getString("data")), null, "N3") ;

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
	UpdateAction.execute(request, m) ;
	
	// Output results
	System.err.println("SparqlRunner: Writing model to STDOUT");
	m.write(System.out, "NT");
	System.err.println("SparqlRunner: DONE");
	
    }
}

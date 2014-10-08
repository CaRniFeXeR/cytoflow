package org.flowcyt.facejava.faceflow.loader;

import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;

import javax.xml.bind.JAXBException;

import org.flowcyt.facejava.compensation.SpilloverMatrixSet;
import org.flowcyt.facejava.compensation.exception.InvalidCompensationMLFileException;
import org.flowcyt.facejava.compensation.xmlio.CompensationMLFileReader;
import org.flowcyt.facejava.faceflow.exception.FileLoaderException;
import org.flowcyt.facejava.fcsdata.exception.DuplicateParameterReferenceException;
import org.flowcyt.facejava.fcsdata.exception.InvalidDataSetsException;
import org.flowcyt.facejava.fcsdata.impl.FcsDataFile;
import org.flowcyt.facejava.fcsdata.io.CFCSInput;
import org.flowcyt.facejava.gating.exception.InvalidGateDescriptionException;
import org.flowcyt.facejava.gating.exception.InvalidGatingMLFileException;
import org.flowcyt.facejava.gating.gates.GateSet;
import org.flowcyt.facejava.gating.xmlio.GatingMLFileReader;
import org.flowcyt.facejava.transformation.TransformationCollection;
import org.flowcyt.facejava.transformation.exception.InvalidTransformationException;
import org.flowcyt.facejava.transformation.exception.InvalidTransformationMLFileException;
import org.flowcyt.facejava.transformation.xmlio.TransformationMLFileReader;
import org.xml.sax.SAXException;

/**
 * <p>
 * URIFileLoaders interpret the location strings as URIs, i.e., the locations are 
 * passed to the URI(String) constructor and the resulting URI objects are
 * used for loading.
 * 
 * @author echng
 */
public class URIFileLoader extends CachingFileLoader {
	
	/**
	 * Constructor. CFCSInput is set to be the default FCSInput to use for loading
	 * FCS Data Files.
	 */
	public URIFileLoader() {
		this.setFcsInput(new CFCSInput());
	}
	
	@Override
	protected SpilloverMatrixSet performCompensationLoad(String location) throws FileLoaderException {
		try {
			CompensationMLFileReader reader = new CompensationMLFileReader(new URI(location));
			return reader.read();
		} catch (JAXBException e) {
			throw new FileLoaderException(e);
		} catch (IOException e) {
			throw new FileLoaderException(e);
		} catch (InvalidCompensationMLFileException e) {
			throw new FileLoaderException(e);
		} catch (SAXException e) {
			throw new FileLoaderException(e);
		} catch (URISyntaxException e) {
			throw new FileLoaderException(e);
		}
	}

	@Override
	protected FcsDataFile performFcsLoad(String location) throws FileLoaderException {
		try {
			return fcsIn.read(new URI(location));
		} catch (IOException e) {
			throw new FileLoaderException(e);
		} catch (InvalidDataSetsException e) {
			throw new FileLoaderException(e);
		} catch (URISyntaxException e) {
			throw new FileLoaderException(e);
		}
	}

	@Override
	protected GateSet performGatingLoad(String location) throws FileLoaderException {
		try {
			GatingMLFileReader reader = new GatingMLFileReader(new URI(location));
			return reader.read();
		} catch (MalformedURLException e) {
			throw new FileLoaderException(e);
		} catch (SAXException e) {
			throw new FileLoaderException(e);
		} catch (JAXBException e) {
			throw new FileLoaderException(e);
		} catch (URISyntaxException e) {
			throw new FileLoaderException(e);
		} catch (InvalidGateDescriptionException e) {
			throw new FileLoaderException(e);
		} catch (InvalidGatingMLFileException e) {
			throw new FileLoaderException(e);
		} catch (IOException e) {
			throw new FileLoaderException(e);
		}		
	}

	@Override
	protected TransformationCollection performTransformationLoad(String location) throws FileLoaderException {
		try {
			TransformationMLFileReader reader = new TransformationMLFileReader(new URI(location));
			return reader.read();
		} catch (MalformedURLException e) {
			throw new FileLoaderException(e);
		} catch (SAXException e) {
			throw new FileLoaderException(e);
		} catch (JAXBException e) {
			throw new FileLoaderException(e);
		} catch (URISyntaxException e) {
			throw new FileLoaderException(e);
		} catch (InvalidTransformationException e) {
			throw new FileLoaderException(e);
		} catch (InvalidTransformationMLFileException e) {
			throw new FileLoaderException(e);
		} catch (DuplicateParameterReferenceException e) {
			throw new FileLoaderException(e);
		} catch (IOException e) {
			throw new FileLoaderException(e);
		}
	}
}

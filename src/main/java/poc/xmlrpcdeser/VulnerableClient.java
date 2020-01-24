package poc.xmlrpcdeser;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.HashMap;
import java.util.Hashtable;
import org.apache.xmlrpc.XmlRpcException;
import org.apache.xmlrpc.client.XmlRpcClient;
import org.apache.xmlrpc.client.XmlRpcClientConfigImpl;

public class VulnerableClient {
    public static void main(String[] args) throws MalformedURLException, XmlRpcException {
        String domainName = "http://127.0.0.1:8888";

        String serverurl = domainName + "/RPC2";
        XmlRpcClientConfigImpl config = new XmlRpcClientConfigImpl();
        config.setServerURL(new URL(serverurl));
        XmlRpcClient client = new XmlRpcClient();
        client.setConfig(config);
        Object[] params = new Object[]{"test", "'tell me you are alive' 1337"};
        Object result = (Object) client.execute("xmlrpc-api", params);
    }
}

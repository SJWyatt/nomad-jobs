# config file version
apiVersion: 1

# list of datasources that should be deleted from the database
deleteDatasources:
  - name: Prometheus
    orgId: 1

# list of datasources to insert/update depending
# whats available in the database
datasources:

- name: Prometheus
  # <string, required> datasource type. Required
  type: prometheus
  
  # <string, required> access mode. direct or proxy. Required
  access: proxy
  
  # <int> org id. will default to orgId 1 if not specified
  orgId: 1
  
  # <string> url
  url: http://{{ range service "prometheus" }}{{ .Address }}:{{ .Port }}{{ end }}
  
  # <string> database password, if used
  password:
  
  # <string> database user, if used
  user:
  
  # <string> database name, if used
  database:
  
  # <bool> enable/disable basic auth
  basicAuth: false
  
  # <string> basic auth username, if used
  basicAuthUser:
  
  # <string> basic auth password, if used
  basicAuthPassword:
  
  # <bool> enable/disable with credentials headers
  withCredentials:
  
  # <bool> mark as default datasource. Max one per org
  isDefault: true
  
  # <map> fields that will be converted to json and stored in json_data
  jsonData:
     graphiteVersion: "1.1"
     tlsAuth: false
     tlsAuthWithCACert: false
  
  # <string> json object of data that will be encrypted.
  secureJsonData:
    tlsCACert: "..."
    tlsClientCert: "..."
    tlsClientKey: "..."
    version: 1
  
  # <bool> allow users to edit datasources from the UI.
  editable: true

- name: InfluxDB
  type: influxdb
  access: proxy
  database: covid19
  user: 
  url: http://{{ range service "influxdb" }}{{ .Address }}:{{ .Port }}{{ end }}
  jsonData:
    timeInterval: "15s"
  secureJsonData:
    password: 
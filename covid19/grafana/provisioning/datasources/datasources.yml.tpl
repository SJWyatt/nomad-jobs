# config file version
apiVersion: 1

# list of datasources to insert/update depending
# whats available in the database
datasources:

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

- name: InfluxDBGlobal
  type: influxdb
  access: proxy
  database: covid19global
  user: 
  url: http://{{ range service "influxdb" }}{{ .Address }}:{{ .Port }}{{ end }}
  jsonData:
    timeInterval: "15s"
  secureJsonData:
    password: 

- name: InfluxDBBases
  type: influxdb
  access: proxy
  database: bases
  user: 
  url: http://{{ range service "influxdb" }}{{ .Address }}:{{ .Port }}{{ end }}
  jsonData:
    timeInterval: "15s"
  secureJsonData:
    password: 

- name: JSON
  type: simpod-json-datasource
  access: proxy
  url: http://{{ range service "sir" }}{{ .Address }}:{{ .Port }}{{ end }}
job "influxdb" {
  datacenters = ["dc1"]

  # Start api group
  group "covid-db" {
    count = 1

		task "covid-db" {
      driver = "docker"

      artifact {
        source      = "https://raw.githubusercontent.com/xaviermerino/nomad-jobs/master/demo/influxdb/influxdb.conf"
        destination = "/local/"
      }

      config {
        image = "influxdb"
        args = [
          "-config", "/etc/influxdb/influxdb.conf"
        ]
        
        port_map {
          http = 8086
        }

        volumes = [
          "/local/influxdb.conf:/etc/influxdb/influxdb.conf"
        ]
      }

      resources {
        cpu = 500 
        memory = 300 
        network {
          mbits = 100
          port "http" {
            static = 8086
            to = 8086
          }
        }
      }

		} # End task

	} # End group

} # End job

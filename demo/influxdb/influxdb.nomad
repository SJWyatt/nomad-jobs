job "inlfuxdb" {
  datacenters = ["dc1"]

  # Start api group
  group "covid-db" {
    count = 1

		task "covid-db" {
      driver = "docker"

      config {
        image = "influxdb"
        port_map {
          http = 8086
        }
      }

      artifact {
        source      = "influxdb.conf"
        destination = "/etc/influxdb/"
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

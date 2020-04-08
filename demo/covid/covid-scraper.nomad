job "covid19" {
	datacenters = ["dc1"]

  # Start api group
  group "collector" {
    count = 1

		// task "scraper" {
    //   driver = "docker"

    //   env {
    //     INFLUX_HOST = "localhost"
    //     INFLUX_DB = "covid19"
    //     INFLUX_DBPORT = 8086
    //     INFLUX_USER = ""
    //     INFLUX_PASS = ""
    //   }

    //   config {
    //     image = "xaviermerino/covid-scraper:latest"
    //   }

    //   resources {
    //     cpu = 500 
    //     memory = 300 
    //     network {
    //       mbits = 100
    //     }
    //   }

		// } # End task

		task "covid-db" {
      driver = "docker"

      config {
        image = "influxdb"
        port_map {
          db = 8086
        }
      }

      resources {
        cpu = 500 
        memory = 300 
        network {
          mbits = 100
          port "db" {
            static = 8086
            to = 8086
          }
        }
      }

      service {
        name = "influxdb"
        port = "db"
        check {
          name     = "InfluxDB HTTP"
          type     = "http"
          path     = "/"
          interval = "5s"
          timeout  = "2s"
           check_restart {
            limit = 2
            grace = "60s"
            ignore_warnings = false
          }
        }
      }

		} # End task

	} # End group

} # End job

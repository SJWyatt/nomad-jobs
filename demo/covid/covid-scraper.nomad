job "scraper" {
	datacenters = ["dc1"]

  # Start api group
  group "scraper" {
    count = 1

		task "scraper" {
      driver = "docker"

      env {
        INFLUX_HOST = "localhost"
        INFLUX_DB = "covid19"
        INFLUX_DBPORT = 8086
        INFLUX_USER = ""
        INFLUX_PASS = ""
      }

      config {
        image = "xaviermerino/covid-scraper:latest"
      }

      resources {
        cpu = 500 
        memory = 300 
        network {
          mbits = 100
        }
      }

		} # End task

	} # End group

} # End job

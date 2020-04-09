job "scraper-us" {
	datacenters = ["dc1"]
  type = "batch"

  periodic {
    cron = "*/15 * * * *"
    prohibit_overlap = true
  }

  group "scraper" {
    count = 1

		task "scraper" {
      driver = "docker"

      template {
        data = <<EOH
INFLUX_HOST = {{ range service "influxdb" }}{{ .Address }}{{ end }}
INFLUX_DB = "covid19"
INFLUX_DBPORT = 8086
INFLUX_USER = ""
INFLUX_PASS = ""
EOH
        destination = "secrets/environment.env"
        env = true
      }

      artifact {
        source      = "https://raw.githubusercontent.com/xaviermerino/demo-covid19-us/master/demo-covid19-us/scraper/covid19.py"
        destination = "/local/scripts"
      }

      artifact {
        source      = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
        destination = "/local/data"
      }

      artifact {
        source      = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"
        destination = "/local/data"
      }
      
      config {
        image = "xaviermerino/covid-scraper:latest"
        volumes = [
          "local/scripts/covid19.py:/root/covid19.py",
          "local/data/time_series_covid19_confirmed_US.csv:/time_series_covid19_confirmed_US.csv",
          "local/data/time_series_covid19_deaths_US.csv:/time_series_covid19_deaths_US.csv"
        ]
        // command = "/bin/bash"
        // args = [
        //   "-c", "while true; do echo 'Waiting...'; sleep 5; done"
        // ]
      }

      resources {
        cpu = 1000 
        memory = 500 
        network {
          mbits = 100
          mode = "host"
        }
      }

		} # End task

	} # End group

} # End job

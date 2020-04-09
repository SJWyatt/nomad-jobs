job "scraper" {
	datacenters = ["dc1"]
  type = "service"

  // periodic {
  //   cron = "*/2 * * * *"
  //   prohibit_overlap = true
  // }

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
        source      = "https://raw.githubusercontent.com/xaviermerino/nomad-jobs/master/demo-covid19-us/scraper/covid19.py"
        destination = "/local/scripts"
      }

      config {
        image = "xaviermerino/covid-scraper:latest"
        volumes = [
          "local/scripts/covid19.py:/root/covid19.py"
        ]
        command = "/bin/bash"
        args = [
          "-c", "while true; do echo 'Waiting...'; sleep 5; done"
        ]
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

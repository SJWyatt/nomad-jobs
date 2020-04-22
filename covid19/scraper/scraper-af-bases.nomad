job "scraper-af-bases-periodic" {
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
INFLUX_DB = "bases"
INFLUX_DBPORT = {{ range service "influxdb" }}{{ .Port }}{{ end }}
INFLUX_USER = ""
INFLUX_PASS = ""
EOH
        destination = "secrets/environment.env"
        env = true
      }

      artifact {
        source      = "https://raw.githubusercontent.com/xaviermerino/nomad-jobs/master/covid19/scraper/src/af-bases.py"
        destination = "/local/scripts"
      }

      artifact {
        source      = "https://raw.githubusercontent.com/xaviermerino/nomad-jobs/master/covid19/scraper/data/af_bases.csv"
        destination = "/local/data"
      }
      
      config {
        image = "xaviermerino/covid-scraper:latest"

        // Name does not change because container hard-coded for covid19.py
        volumes = [
          "local/scripts/af-bases.py:/root/covid19.py",
          "local/data/af_bases.csv:/root/af_bases.csv"
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
          mode = "bridge"
        }
      }

		} # End task

	} # End group

} # End job

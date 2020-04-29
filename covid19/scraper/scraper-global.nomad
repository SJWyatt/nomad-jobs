job "scraper-global-periodic" {
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
INFLUX_DB = "covid19global"
INFLUX_DBPORT = {{ range service "influxdb" }}{{ .Port }}{{ end }}
INFLUX_USER = ""
INFLUX_PASS = ""
EOH
        destination = "secrets/environment.env"
        env = true
      }

      artifact {
        source      = "https://raw.githubusercontent.com/xaviermerino/nomad-jobs/master/covid19/scraper/src/covid19-global.py"
        destination = "/local/scripts"
      }
      
      config {
        image = "xaviermerino/covid-scraper:latest"
        volumes = [
          "local/scripts/covid19-global.py:/root/covid19.py"
        ]
        // command = "/bin/bash"
        // args = [
        //   "-c", "while true; do echo 'Waiting...'; sleep 5; done"
        // ]
      }

      resources {
        cpu = 1000 
        memory = 512 
        network {
          mbits = 100
          mode = "bridge"
        }
      }

		} # End task

	} # End group

} # End job

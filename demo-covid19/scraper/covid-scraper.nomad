job "scraper-bathc" {
	datacenters = ["dc1"]
  type = "batch"

  periodic {
    cron = "*/5 * * * *"
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
        source      = "https://raw.githubusercontent.com/xaviermerino/nomad-jobs/master/demo-covid19/scraper/covid19.py"
        destination = "/local/scripts"
      }

      config {
        image = "xaviermerino/covid-scraper:latest"
        command = "/bin/bash"
        // args = [
        //   "-c", "while true; do echo 'Hit CTRL+C'; sleep 1; done"
        // ]
        volumes = [
          "local/scripts/covid19.py:/root/covid19.py"
        ]
        #dns_servers = ["172.17.0.1", "8.8.8.8"]
      }

      resources {
        cpu = 500 
        memory = 300 
        network {
          mbits = 100
          mode = "host"
        }
      }

		} # End task

	} # End group

} # End job

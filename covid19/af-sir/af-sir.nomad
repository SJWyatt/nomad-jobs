job "scraper-af-sir-periodic" {
	datacenters = ["dc1"]
  type = "service"

  group "scraper-af-sir-periodic" {
    count = 1

		task "scraper-af-sir-periodic" {
      driver = "docker"

      template {
        data = <<EOH
INFLUX_HOST = {{ range service "influxdb" }}{{ .Address }}{{ end }}
INFLUX_DB = "military_sir"
INFLUX_DBPORT = {{ range service "influxdb" }}{{ .Port }}{{ end }}
INFLUX_USER = ""
INFLUX_PASS = ""
EOH
        destination = "secrets/environment.env"
        env = true
      }

      artifact {
        source      = "github.com/xaviermerino/nomad-jobs/covid19/af-sir/src"
        destination = "/local/scripts/"
      }

      artifact {
        source      = "github.com/xaviermerino/nomad-jobs/covid19/af-sir/Data"
        destination = "/local/data/"
      }

      config {
        image = "xaviermerino/covid-af-sir:latest"

        volumes = [
          "local/data/census/PEP_2018_PEPAGESEX_with_ann.csv:/root/Data/census/PEP_2018_PEPAGESEX_with_ann.csv",
          "local/data/covid_kaggle/usa_county_wise.csv:/root/Data/covid_kaggle/usa_county_wise.csv",
          "local/scripts/dataPreProcess.py:/root/dataPreProcess.py",
          "local/scripts/ingest_military.py:/root/ingest_military.py",
          "local/scripts/LocationResolver.py:/root/LocationResolver.py",
          "local/scripts/sir.py:/root/sir.py",
          "local/scripts/sirquery.py:/root/sirquery.py",
        ]

        command = "/bin/bash"
        args = [
          "-c", "while true; do echo 'Waiting...'; sleep 5; done"
        ]
      }

      resources {
        cpu = 2000 
        memory = 1024 
        network {
          mbits = 100
          mode = "bridge"
        }
      }

      

		} # End task

	} # End group

} # End job

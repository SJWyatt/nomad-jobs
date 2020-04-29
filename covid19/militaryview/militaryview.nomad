job "api-militaryview" {
	datacenters = ["dc1"]
  type = "service"

  group "api-militaryview" {
    count = 1

		task "api-militaryview" {
      driver = "docker"

      template {
        data = <<EOH
INFLUX_HOST = {{ range service "influxdb" }}{{ .Address }}{{ end }}
INFLUX_DBPORT = {{ range service "influxdb" }}{{ .Port }}{{ end }}
EOH
        destination = "secrets/environment.env"
        env = true
      }

      artifact {
        source      = "github.com/xaviermerino/nomad-jobs/covid19/militaryview/src"
        destination = "/local/scripts/"
      }

      artifact {
        source      = "github.com/xaviermerino/nomad-jobs/covid19/militaryview/Data"
        destination = "/local/data/"
      }

      config {
        image = "xaviermerino/covid-af-sir:latest"

        volumes = [
          "local/data/census/PEP_2018_PEPAGESEX_with_ann.csv:/root/Data/census/PEP_2018_PEPAGESEX_with_ann.csv",
          "local/data/covid_kaggle/usa_county_wise.csv:/root/Data/covid_kaggle/usa_county_wise.csv",
          "local/scripts/dataPreProcess.py:/root/dataPreProcess.py",
          "local/scripts/mapquery.py:/root/mapquery.py",
          "local/scripts/LocationResolver.py:/root/LocationResolver.py",
          "local/scripts/sir.py:/root/sir.py",
          "local/scripts/sirquery.py:/root/sirquery.py",
          "local/scripts/api_military.py:/root/api_military.py",
          "local/data/api_sir_model.csv:/root/Data/api_sir_model.csv",
          "local/data/full_state_sir.csv:/root/Data/full_state_sir.csv",
          "local/data/resource_usage.csv:/root/Data/resource_usage.csv",
          "local/data/sir_model.csv:/root/Data/sir_model.csv"
        ]

        command = "gunicorn"
        args = [
          "-b", "0.0.0.0:5050", "api_military:app", "-w", "1"
        ]
        // command = "/bin/bash"
        // args = [
        //   "-c", "while true; do echo 'Waiting...'; sleep 5; done"
        // ]
      }

      resources {
        cpu = 2500 
        memory = 512 
        network {
          mbits = 100
          mode = "bridge"
        }
      }

      

		} # End task

	} # End group

} # End job

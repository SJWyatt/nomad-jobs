job "milview" {
  datacenters = ["dc1"]
  type = "service"

  group "milview" {
    count = 1

		task "milview" {
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
        source      = "github.com/xaviermerino/nomad-jobs/covid19/milview/src"
        destination = "/local/scripts/"
      }
      
      config {
        image = "xaviermerino/covid-milview:latest"
        command = "gunicorn"
        args = [
          "-b", "0.0.0.0:5050", "map-api:app", "-w", "1"
        ]

        // command = "/bin/bash"
        // args = [
        //   "-c", "while true; do echo 'Waiting...'; sleep 5; done"
        // ]

        volumes = [
          "local/scripts/map-api.py:/root/map-api.py",
          "local/scripts/mapquery.py:/root/mapquery.py"
        ]

        port_map {
          http = 5050
        }
      }

      resources {
        cpu = 2000 
        memory = 1024 
        network {
          mbits = 100
          mode = "bridge"
          port "http" {
            # dev mode
            static = 5051
          }
        }
      }

      service {
        name = "milview"
        port = "http"
      }

		} # End task

	} # End group

} # End job

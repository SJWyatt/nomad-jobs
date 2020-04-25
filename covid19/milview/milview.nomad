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
INFLUX_PORT = {{ range service "influxdb" }}{{ .Port }}{{ end }}
EOH
        destination = "secrets/environment.env"
        env = true
      }

      artifact {
        source      = "github.com/xaviermerino/nomad-jobs/covid19/milview/src"
        destination = "/root/"
      }
      
      config {
        image = "xaviermerino/covid-milview:latest"
        command = "gunicorn"
        args = [
          "-b", "0.0.0.0:5050", "map-api:app", "-w", "1"
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

job "grafana" {
  datacenters = ["dc1"]
  type = "service"

  group "grafana" {

    task "grafana" {
      driver = "docker"
      config {
        image = "grafana/grafana"
      }

      env {
        GF_LOG_LEVEL = "DEBUG"
        GF_LOG_MODE = "console"
        GF_SERVER_HTTP_PORT = "${NOMAD_PORT_http}"
        GF_PATHS_PROVISIONING = "/local/provisioning"
        GF_INSTALL_PLUGINS = "grafana-world-map"
      }

      artifact {
        source      = "github.com/xaviermerino/nomad-jobs/demo-covid19/grafana/provisioning"
        destination = "local/provisioning/"
      }

      artifact {
        source      = "github.com/xaviermerino/nomad-jobs/demo-covid19/grafana/dashboards"
        destination = "local/dashboards/"
      }

      template {
        source = "local/provisioning/datasources/datasources.yml.tpl"
        destination = "local/provisioning/datasources/datasources.yml"
      }

      resources {
        cpu    = 1000
        memory = 256
        network {
          mbits = 10
          mode = "host"
          port "http" {}
        }
      }

      service {
        name = "grafana"
        port = "http"
        check {
          name     = "Grafana HTTP"
          type     = "http"
          path     = "/api/health"
          interval = "5s"
          timeout  = "2s"
           check_restart {
            limit = 2
            grace = "60s"
            ignore_warnings = false
          }
        }
      }
    }
  }
}

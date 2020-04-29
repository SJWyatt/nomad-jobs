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
        GF_INSTALL_PLUGINS = "grafana-worldmap-panel,simpod-json-datasource,https://packages.hiveeyes.org/grafana/grafana-map-panel/grafana-map-panel-0.9.0.zip;grafana-map-panel"
      }

      artifact {
        source      = "github.com/xaviermerino/nomad-jobs/covid19/grafana/provisioning"
        destination = "local/provisioning/"
      }

      artifact {
        source      = "github.com/xaviermerino/nomad-jobs/covid19/grafana/dashboards"
        destination = "local/dashboards/"
      }

      template {
        source = "local/provisioning/datasources/datasources.yml.tpl"
        destination = "local/provisioning/datasources/datasources.yml"
        change_mode = "noop"
      }

      resources {
        cpu    = 4000
        memory = 2048
        network {
          mbits = 100
          mode = "host"
          port "http" {
            static = 3000
          }
        }
      }

      service {
        name = "grafana"
        port = "http"
        tags = ["urlprefix-/"]
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

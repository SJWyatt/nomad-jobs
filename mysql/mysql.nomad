job "mysql" {
  datacenters = ["dc1"]
  type = "service"

  group "mysql" {
    task "mysql" {
      driver = "docker"
      config {
        image = "mysql"
      }

      env {
        MYSQL_ROOT_PASSWORD = "iamgroot"
        MYSQL_DATABASE = "covid19"
      }

      artifact {
        source      = "https://medium.com/faun/using-mysql-on-docker-e6c6216c91e1"
        destination = "/var/lib/mysql-files"
      }

      artifact {
        source      = "github=link"
        destination = "/local/script"
      }

    //   artifact {
    //     source      = "github.com/xaviermerino/nomad-jobs/grafana/dashboards"
    //     destination = "local/dashboards/"
    //   }

    //   template {
    //     source = "local/provisioning/datasources/prometheus.yml.tpl"
    //     destination = "local/provisioning/datasources/prometheus.yml"
    //   }

      resources {
        cpu    = 1000
        memory = 256
        network {
          mbits = 10
          mode = "host"
          port "http" {}
        }
      }

    }
  }
}

job "mysql" {
  datacenters = ["dc1"]
  type = "service"

  group "mysql" {
    task "mysql" {
      driver = "docker"
      
      env {
        MYSQL_ROOT_PASSWORD = "iamgroot"
        MYSQL_DATABASE = "geolocations"
        MYSQL_ROOT_HOST= "%"
      }

      artifact {
        source      = "https://raw.githubusercontent.com/xaviermerino/nomad-jobs/master/covid19/mysql/data/af_bases.csv"
        destination = "/local/data/"
      }

      artifact {
        source      = "https://raw.githubusercontent.com/xaviermerino/nomad-jobs/master/covid19/mysql/conf/ingest.sql"
        destination = "/local/conf/"
      }

      artifact {
        source      = "https://raw.githubusercontent.com/xaviermerino/nomad-jobs/master/covid19/mysql/conf/my.cnf"
        destination = "/local/conf/"
      }

      config {
        image = "mysql"

        volumes = [
          "local/conf/ingest.sql:/docker-entrypoint-initdb.d/ingest.sql",
          "local/conf/my.cnf:/etc/mysql/my.cnf"
        ]

        port_map {
          http = 3306
        }
      }

      resources {
        cpu    = 2400
        memory = 1024

        network {
          mbits = 100
          mode = "host"
          port "http" {
            static = 3306
          }
        }

      }

    }
  }
}

# 📊 Zoi Monitoring Stack

Comprehensive monitoring solution with Prometheus, Grafana, and specialized exporters for system, container, database, and GPU metrics.

## 🏗️ Architecture

### Core Monitoring Services
- **Prometheus** → Metrics collection, storage, and alerting engine
- **Grafana** → Visualization dashboards and analytics
- **AlertManager** → Alert routing and notification management

### System & Infrastructure Exporters
- **Node Exporter** → Host system metrics (CPU, RAM, Disk, Network)
- **cAdvisor** → Container resource usage and performance metrics
- **Redis Exporter** → Redis performance and memory metrics
- **Postgres Exporter** → PostgreSQL database performance metrics
- **NVIDIA GPU Exporter** → GPU utilization, memory, and temperature metrics

## 🌐 Service Endpoints

| Service | URL | Port | Purpose |
|---------|-----|------|---------|
| **Prometheus** | http://localhost:7100 | 7100 | Metrics collection & queries |
| **Grafana** | http://localhost:7101 | 7101 | Dashboards & visualization |
| **Node Exporter** | http://localhost:7102 | 7102 | System metrics endpoint |
| **cAdvisor** | http://localhost:7103 | 7103 | Container metrics UI |
| **Redis Exporter** | http://localhost:7104 | 7104 | Redis metrics endpoint |
| **Postgres Exporter** | http://localhost:7105 | 7105 | PostgreSQL metrics endpoint |
| **AlertManager** | http://localhost:7106 | 7106 | Alert management UI |
| **NVIDIA GPU Exporter** | http://localhost:7107 | 7107 | GPU metrics endpoint |

### Traefik Integration
Services are also available via domain routing:
- **Prometheus**: http://prometheus.zoi.local
- **Grafana**: http://grafana.zoi.local
- **cAdvisor**: http://cadvisor.zoi.local
- **AlertManager**: http://alertmanager.zoi.local
- **NVIDIA Exporter**: http://nvidia.zoi.local

## 🚀 Quick Start

### Prerequisites
```powershell
# For GPU monitoring (optional)
nvidia-smi  # Verify NVIDIA drivers are installed
docker --version  # Ensure Docker with NVIDIA runtime support
```

### 1. Start Monitoring Stack
```powershell
# Start all monitoring services
docker compose up -d

# Check service status
docker compose ps
```

### 2. Access Dashboards
```powershell
# Open Grafana (default: admin/admin123)
start http://localhost:7101

# Open Prometheus
start http://localhost:7100

# Check GPU metrics (if available)
curl http://localhost:7107/metrics
```

### 3. Verify Metrics Collection
```powershell
# Check Prometheus targets
curl http://localhost:7100/api/v1/targets

# Test a simple query
curl "http://localhost:7100/api/v1/query?query=up"
```

## 🎯 Key Metrics Collected

### 🖥️ System Metrics (Node Exporter)
- **CPU**: Usage, load average, context switches
- **Memory**: Available, used, cached, swap
- **Disk**: I/O operations, space usage, read/write rates
- **Network**: Bytes sent/received, packet rates, errors

### 🐳 Container Metrics (cAdvisor)
- **Resource Usage**: CPU, memory, network per container
- **Performance**: Throttling, OOM kills, restart counts
- **Storage**: Filesystem usage and I/O per container

### 🗄️ Database Metrics
**PostgreSQL** (Postgres Exporter):
- Connection counts, query performance, lock waits
- Database size, transaction rates, cache hit ratios

**Redis** (Redis Exporter):
- Memory usage, key counts, command statistics
- Replication lag, persistence metrics

### 🎮 GPU Metrics (NVIDIA Exporter)
- **Utilization**: GPU and memory usage percentages
- **Temperature**: GPU core and memory temperatures
- **Power**: Power consumption and limits
- **Memory**: Total, used, and free GPU memory
- **Processes**: Running GPU processes and their memory usage

## 🔧 Configuration

### Grafana Setup
1. **Login**: http://localhost:7101 (admin/admin123)
2. **Add Prometheus Data Source**: http://prometheus:9090
3. **Import Dashboards**: Pre-configured dashboards available

### Prometheus Configuration
- **Config**: `./config/prometheus/prometheus.yml`
- **Rules**: `./config/prometheus/rules/`
- **Retention**: 30 days, 10GB max

### GPU Monitoring Requirements
**For NVIDIA GPU monitoring**:
```powershell
# Verify NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Check GPU exporter metrics
curl http://localhost:7107/metrics | findstr nvidia
```

**If GPU not available**:
- GPU exporter will show as unhealthy (expected)
- All other monitoring continues to work normally
- Remove GPU exporter service if not needed

## 📈 Dashboard Recommendations

### System Overview Dashboard
- CPU, Memory, Disk usage across all hosts
- Network traffic and error rates
- Container resource consumption

### AI/LLM Workload Dashboard
- GPU utilization and memory usage
- vLLM container performance metrics
- LiteLLM request rates and response times
- Model inference latencies

### Database Performance Dashboard
- PostgreSQL connection pools and query performance
- Redis memory usage and command rates
- Database-specific metrics for each service

### Infrastructure Health Dashboard
- Service uptime and availability
- Container restart counts and health checks
- Alert status and recent notifications

## 🚨 Alerting

### Pre-configured Alerts
- **High CPU Usage**: >80% for 5 minutes
- **Low Memory**: <10% available for 5 minutes
- **Disk Space**: <10% free space
- **Container Down**: Service unavailable for 1 minute
- **GPU Temperature**: >85°C for 2 minutes
- **Database Connections**: >90% of max connections

### Alert Channels
Configure in `./config/alertmanager/alertmanager.yml`:
- Email notifications
- Slack/Discord webhooks
- PagerDuty integration
- Custom webhook endpoints

## 🔍 Troubleshooting

### Service Health Checks
```powershell
# Check all services
docker compose ps

# View service logs
docker compose logs [service-name]

# Test metric endpoints
curl http://localhost:7100/-/healthy  # Prometheus
curl http://localhost:7101/api/health  # Grafana
```

### Common Issues

**GPU Exporter Not Working**:
```powershell
# Check NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Verify GPU exporter logs
docker compose logs nvidia-gpu-exporter

# Test GPU metrics manually
curl http://localhost:7107/metrics
```

**Database Exporters Connection Issues**:
```powershell
# Test PostgreSQL connection
docker exec -it postgres-exporter /bin/sh -c "wget -qO- http://localhost:9187/metrics"

# Test Redis connection
docker exec -it redis-exporter /bin/sh -c "wget -qO- http://localhost:9121/metrics"
```

**Prometheus Targets Down**:
```powershell
# Check target status
curl http://localhost:7100/api/v1/targets

# Verify network connectivity
docker network inspect zoi-monitoring_monitoring_network
```

## 📊 Performance & Resource Usage

### Resource Requirements

| Service | CPU | RAM | Storage | Notes |
|---------|-----|-----|---------|-------|
| Prometheus | 1-2 cores | 2-4GB | 10-50GB | Scales with metrics |
| Grafana | 0.5 core | 512MB | 1GB | Lightweight |
| Node Exporter | 0.1 core | 50MB | 10MB | Very lightweight |
| cAdvisor | 0.2 core | 100MB | 50MB | Per-container overhead |
| GPU Exporter | 0.1 core | 50MB | 10MB | Minimal overhead |
| Exporters (each) | 0.1 core | 50MB | 10MB | Database-dependent |

### Optimization Tips
1. **Prometheus Retention**: Adjust based on storage capacity
2. **Scrape Intervals**: Balance between granularity and performance
3. **Dashboard Queries**: Optimize for faster loading
4. **Alert Rules**: Avoid overly complex queries
5. **GPU Monitoring**: Only enable if GPUs are available

---

**📊 Your comprehensive monitoring stack is ready to provide full visibility into your Zoi ecosystem!**

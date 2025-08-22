# Zoi Monitoring Stack Setup Guide

**Status:** ✅ Ready for deployment  
**Components:** Prometheus + Grafana + AlertManager + Exporters  
**Integration:** Full LiteLLM cost tracking + system monitoring

## Overview

This monitoring stack provides comprehensive observability for your Zoi system, including:
- **Cost Tracking**: Real-time LiteLLM model costs and usage
- **System Monitoring**: CPU, memory, disk, network metrics
- **Container Monitoring**: Docker container resource usage
- **Database Monitoring**: PostgreSQL and Redis metrics
- **Application Monitoring**: FastAPI, Traefik, and service health
- **Alerting**: Proactive alerts for issues and cost overruns

## Quick Start

### 1. Setup Monitoring Stack
```powershell
# Run the setup script
.\setup-monitoring.ps1 -StartServices

# Or manually start services
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. Access Dashboards
- **Grafana**: http://grafana.zoi.local (admin/admin123)
- **Prometheus**: http://prometheus.zoi.local
- **AlertManager**: http://alertmanager.zoi.local

## Components

### 🔍 **Prometheus** (Port 9090)
- **Purpose**: Metrics collection and storage
- **Retention**: 30 days, 10GB max
- **Scrape Interval**: 15s (10s for LiteLLM)
- **Targets**: All services + system metrics

### 📊 **Grafana** (Port 3000)
- **Purpose**: Visualization and dashboards
- **Credentials**: admin/admin123
- **Dashboards**: Pre-configured for LiteLLM and system monitoring
- **Plugins**: Pie chart, world map, clock panels

### 🚨 **AlertManager** (Port 9093)
- **Purpose**: Alert routing and notifications
- **Channels**: Webhook, email (configurable)
- **Grouping**: By service, severity, and alert type
- **Routing**: Critical alerts get immediate notification

### 📈 **Node Exporter** (Port 9100)
- **Purpose**: System metrics (CPU, memory, disk, network)
- **Metrics**: Hardware and OS metrics
- **Collection**: Host system monitoring

### 🐳 **cAdvisor** (Port 8080)
- **Purpose**: Container metrics
- **Metrics**: Container resource usage, performance
- **Integration**: Docker container monitoring

### 🔧 **Database Exporters**
- **Redis Exporter** (Port 9121): Redis performance metrics
- **Postgres Exporter** (Port 9187): PostgreSQL database metrics

## Key Metrics Monitored

### 💰 **LiteLLM Cost Tracking**
- Real-time cost per model
- Token usage (input/output)
- Request rates and latency
- Error rates by model
- Cost trends and projections

### 🖥️ **System Resources**
- CPU usage per core
- Memory utilization
- Disk space and I/O
- Network traffic
- System load averages

### 🐳 **Container Metrics**
- Container CPU/memory usage
- Container restart counts
- Resource limits and usage
- Container health status

### 🗄️ **Database Performance**
- PostgreSQL connections and queries
- Redis memory usage and operations
- Database response times
- Connection pool status

## Alerting Rules

### 🚨 **Critical Alerts** (Immediate notification)
- Service downtime (LiteLLM, PostgreSQL, Redis)
- System resource exhaustion (>90% memory, <10% disk)
- High error rates (>5%)

### ⚠️ **Warning Alerts** (5-minute delay)
- High resource usage (>80% CPU, >85% memory)
- Elevated response times (>30s)
- Cost threshold breaches
- Container restarts

### 💰 **Cost Alerts**
- Hourly cost >$10
- Daily cost trends
- Unusual spending patterns
- Model-specific cost spikes

## Configuration Files

### Core Configuration
- `docker-compose.monitoring.yml` - Main monitoring stack
- `config/prometheus/prometheus.yml` - Prometheus configuration
- `config/prometheus/rules/zoi-alerts.yml` - Alerting rules
- `config/alertmanager/alertmanager.yml` - Alert routing
- `config/grafana/provisioning/` - Grafana auto-configuration

### Dashboards
- `config/grafana/dashboards/litellm/cost-tracking.json` - LiteLLM dashboard
- Additional dashboards auto-imported from Grafana community

## Management Commands

### Start/Stop Services
```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Stop monitoring stack
docker-compose -f docker-compose.monitoring.yml down

# View logs
docker-compose -f docker-compose.monitoring.yml logs -f

# Check status
docker-compose -f docker-compose.monitoring.yml ps
```

### Maintenance
```bash
# Update images
docker-compose -f docker-compose.monitoring.yml pull
docker-compose -f docker-compose.monitoring.yml up -d

# Backup Grafana dashboards
docker exec grafana grafana-cli admin export-dashboard

# Reload Prometheus config
curl -X POST http://localhost:9090/-/reload
```

## Integration with Existing Services

### ✅ **Already Integrated**
- **LiteLLM**: Prometheus metrics enabled, cost tracking active
- **Traefik**: Metrics endpoint configured (port 8082)
- **PostgreSQL**: Database exporter configured
- **Redis**: Redis exporter configured

### 🔧 **Additional Integration Points**
- **FastAPI**: Add `/metrics` endpoint for application metrics
- **Ollama**: Enable metrics if available
- **vLLM**: Enable metrics if available
- **Qdrant**: Vector database metrics

## Cost Monitoring Features

### 📊 **Real-time Dashboards**
- Cost per model over time
- Token usage trends
- Request volume by model
- Cost efficiency metrics

### 🎯 **Cost Optimization**
- Identify expensive models
- Track usage patterns
- Monitor cost per request
- Budget tracking and alerts

### 📈 **Reporting**
- Daily/weekly/monthly cost reports
- Model performance vs cost analysis
- Usage trend analysis
- Cost forecasting

## Security Considerations

### 🔒 **Access Control**
- Grafana admin authentication
- Prometheus query restrictions
- Network isolation via Docker networks
- No external exposure by default

### 🛡️ **Data Protection**
- Metrics data retention policies
- No sensitive data in metrics
- Secure inter-service communication
- Regular security updates

## Troubleshooting

### Common Issues
1. **Services not starting**: Check Docker networks and dependencies
2. **Metrics not appearing**: Verify service endpoints and firewall
3. **High resource usage**: Adjust scrape intervals and retention
4. **Alert spam**: Fine-tune alert thresholds and grouping

### Health Checks
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Grafana health
curl http://localhost:3000/api/health

# Check AlertManager status
curl http://localhost:9093/api/v1/status
```

## Next Steps

1. **Deploy monitoring stack** using the setup script
2. **Configure custom dashboards** for specific needs
3. **Set up notification channels** (email, Slack, etc.)
4. **Fine-tune alert thresholds** based on usage patterns
5. **Add custom metrics** from your applications
6. **Set up log aggregation** (ELK stack) for comprehensive observability

## Benefits

✅ **Complete visibility** into system performance and costs  
✅ **Proactive alerting** prevents issues before they impact users  
✅ **Cost optimization** through detailed usage tracking  
✅ **Performance monitoring** ensures optimal model performance  
✅ **Historical data** for capacity planning and trend analysis  
✅ **Automated setup** with minimal manual configuration required

The monitoring stack is now ready for deployment and will provide comprehensive observability for your Zoi system!

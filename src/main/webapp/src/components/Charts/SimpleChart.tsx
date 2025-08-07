import React from 'react';
import { Card, Progress, Statistic, Row, Col, Typography } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import './SimpleChart.css';

const { Text } = Typography;

interface ChartData {
  label: string;
  value: number;
  percentage?: number;
  trend?: 'up' | 'down' | 'neutral';
  color?: string;
}

interface SimpleChartProps {
  data: ChartData[];
  title?: string;
  type?: 'bar' | 'line' | 'pie';
  height?: number;
}

export const SimpleBarChart: React.FC<{ data: ChartData[]; title?: string; height?: number }> = ({ 
  data, 
  title,
  height = 300 
}) => {
  const maxValue = Math.max(...data.map(d => d.value));

  return (
    <Card title={title} className="simple-chart-card">
      <div className="simple-bar-chart" style={{ height }}>
        {data.map((item, index) => (
          <div key={index} className="bar-item">
            <div className="bar-container">
              <div 
                className="bar-fill"
                style={{ 
                  height: `${(item.value / maxValue) * 100}%`,
                  backgroundColor: item.color || '#1890ff'
                }}
              >
                <span className="bar-value">{item.value.toFixed(0)}</span>
              </div>
            </div>
            <div className="bar-label">{item.label}</div>
          </div>
        ))}
      </div>
    </Card>
  );
};

export const SimplePieChart: React.FC<{ data: ChartData[]; title?: string }> = ({ 
  data, 
  title 
}) => {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  
  let currentAngle = -90; // Start from top
  
  const slices = data.map((item, index) => {
    const percentage = (item.value / total) * 100;
    const angle = (percentage / 100) * 360;
    const startAngle = currentAngle;
    const endAngle = currentAngle + angle;
    currentAngle = endAngle;
    
    const isLarge = angle > 180 ? 1 : 0;
    const x1 = 50 + 40 * Math.cos((startAngle * Math.PI) / 180);
    const y1 = 50 + 40 * Math.sin((startAngle * Math.PI) / 180);
    const x2 = 50 + 40 * Math.cos((endAngle * Math.PI) / 180);
    const y2 = 50 + 40 * Math.sin((endAngle * Math.PI) / 180);
    
    const colors = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1'];
    const color = item.color || colors[index % colors.length];
    
    return {
      path: `M 50 50 L ${x1} ${y1} A 40 40 0 ${isLarge} 1 ${x2} ${y2} Z`,
      color,
      label: item.label,
      value: item.value,
      percentage
    };
  });

  return (
    <Card title={title} className="simple-chart-card">
      <div className="simple-pie-chart">
        <svg viewBox="0 0 100 100" className="pie-svg">
          {slices.map((slice, index) => (
            <path
              key={index}
              d={slice.path}
              fill={slice.color}
              className="pie-slice"
              data-tooltip={`${slice.label}: ${slice.percentage.toFixed(1)}%`}
            />
          ))}
        </svg>
        <div className="pie-legend">
          {slices.map((slice, index) => (
            <div key={index} className="legend-item">
              <span 
                className="legend-color" 
                style={{ backgroundColor: slice.color }}
              />
              <span className="legend-label">{slice.label}</span>
              <span className="legend-value">{slice.percentage.toFixed(1)}%</span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};

export const SimpleLineChart: React.FC<{ data: ChartData[]; title?: string; height?: number }> = ({ 
  data, 
  title,
  height = 300 
}) => {
  const maxValue = Math.max(...data.map(d => d.value));
  const minValue = Math.min(...data.map(d => d.value));
  const range = maxValue - minValue;

  const points = data.map((item, index) => {
    const x = (index / (data.length - 1)) * 100;
    const y = 100 - ((item.value - minValue) / range) * 100;
    return { x, y, ...item };
  });

  const pathData = points
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
    .join(' ');

  return (
    <Card title={title} className="simple-chart-card">
      <div className="simple-line-chart" style={{ height }}>
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="line-svg">
          <defs>
            <linearGradient id="lineGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" style={{ stopColor: '#1890ff', stopOpacity: 0.3 }} />
              <stop offset="100%" style={{ stopColor: '#1890ff', stopOpacity: 0 }} />
            </linearGradient>
          </defs>
          
          {/* Grid lines */}
          {[0, 25, 50, 75, 100].map(y => (
            <line
              key={y}
              x1="0"
              y1={y}
              x2="100"
              y2={y}
              stroke="#f0f0f0"
              strokeWidth="0.5"
            />
          ))}
          
          {/* Area under line */}
          <path
            d={`${pathData} L 100 100 L 0 100 Z`}
            fill="url(#lineGradient)"
          />
          
          {/* Line */}
          <path
            d={pathData}
            fill="none"
            stroke="#1890ff"
            strokeWidth="2"
          />
          
          {/* Points */}
          {points.map((point, index) => (
            <circle
              key={index}
              cx={point.x}
              cy={point.y}
              r="3"
              fill="#1890ff"
              className="line-point"
              data-tooltip={`${point.label}: ${point.value.toFixed(2)}`}
            />
          ))}
        </svg>
        
        <div className="line-labels">
          {data.map((item, index) => (
            <div key={index} className="line-label-item">
              <Text type="secondary" style={{ fontSize: '12px' }}>{item.label}</Text>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};

export const MiniSparkline: React.FC<{ data: number[]; color?: string; showTrend?: boolean }> = ({ 
  data, 
  color = '#1890ff',
  showTrend = true 
}) => {
  const maxValue = Math.max(...data);
  const minValue = Math.min(...data);
  const range = maxValue - minValue || 1;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * 100;
    const y = 100 - ((value - minValue) / range) * 100;
    return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
  }).join(' ');

  const trend = data[data.length - 1] > data[0] ? 'up' : 'down';

  return (
    <div className="mini-sparkline">
      <svg viewBox="0 0 100 30" className="sparkline-svg">
        <path
          d={points}
          fill="none"
          stroke={color}
          strokeWidth="2"
        />
      </svg>
      {showTrend && (
        <span className={`trend-indicator ${trend}`}>
          {trend === 'up' ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
        </span>
      )}
    </div>
  );
};

export const ProgressChart: React.FC<{ 
  title: string; 
  value: number; 
  target: number; 
  unit?: string;
  color?: string;
}> = ({ 
  title, 
  value, 
  target, 
  unit = '',
  color
}) => {
  const percentage = Math.min((value / target) * 100, 100);
  const isAchieved = value >= target;

  return (
    <Card className="progress-chart-card">
      <Statistic
        title={title}
        value={value}
        suffix={unit}
        valueStyle={{ color: isAchieved ? '#52c41a' : color }}
      />
      <Progress
        percent={percentage}
        strokeColor={isAchieved ? '#52c41a' : color}
        format={() => `${percentage.toFixed(1)}%`}
      />
      <Text type="secondary" style={{ fontSize: '12px' }}>
        Target: {target}{unit}
      </Text>
    </Card>
  );
};

export const ComparisonChart: React.FC<{
  data: Array<{
    label: string;
    current: number;
    previous: number;
    unit?: string;
  }>;
  title?: string;
}> = ({ data, title }) => {
  return (
    <Card title={title} className="comparison-chart-card">
      <Row gutter={[16, 16]}>
        {data.map((item, index) => {
          const change = ((item.current - item.previous) / item.previous) * 100;
          const isPositive = change >= 0;
          
          return (
            <Col span={8} key={index}>
              <div className="comparison-item">
                <Text type="secondary">{item.label}</Text>
                <Statistic
                  value={item.current}
                  suffix={item.unit}
                  valueStyle={{ fontSize: '20px' }}
                />
                <div className="comparison-change">
                  <Text type={isPositive ? 'success' : 'danger'}>
                    {isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                    {Math.abs(change).toFixed(1)}%
                  </Text>
                  <Text type="secondary" style={{ fontSize: '11px' }}>
                    vs {item.previous}{item.unit}
                  </Text>
                </div>
              </div>
            </Col>
          );
        })}
      </Row>
    </Card>
  );
};

export default SimpleBarChart;
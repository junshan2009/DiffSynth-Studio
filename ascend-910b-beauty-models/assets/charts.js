// assets/charts.js
(function () {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();

  // --- Chart: 部署难度 x 美颜效果 scatter ---
  // data: [部署难度(越小越易), 美颜效果, 推理成本(气泡大小), 名称, 类别]
  var data = [
    [1.5, 3.5, 22, 'AutoRetouch', '端到端修图'],
    [2.0, 4.0, 26, 'DRN', '端到端修图'],
    [1.5, 3.0, 22, 'ESSNet', '端到端修图'],
    [3.5, 4.5, 34, 'GFPGAN', '人脸增强'],
    [3.0, 4.5, 34, 'CodeFormer', '人脸增强'],
    [4.0, 5.0, 44, 'OSDFace', '扩散类'],
    [5.0, 5.0, 52, 'DiffRetouch', '扩散类']
  ];

  var categoryColor = {};
  categoryColor['端到端修图'] = accent2;
  categoryColor['人脸增强'] = accent;
  categoryColor['扩散类'] = muted;

  var el = document.getElementById('chart-scatter');
  if (!el || typeof echarts === 'undefined') return;

  var chart = echarts.init(el, null, { renderer: 'svg' });
  chart.setOption({
    animation: false,
    tooltip: {
      appendToBody: true,
      formatter: function (p) {
        var d = p.data;
        return '<strong>' + d[3] + '</strong> (' + d[4] + ')<br/>' +
          '部署难度: ' + d[0] + ' / 5(越小越易)<br/>' +
          '美颜效果: ' + d[1] + ' / 5<br/>' +
          '推理成本: ' + (d[2] >= 40 ? '高' : (d[2] >= 30 ? '中' : '低'));
      }
    },
    legend: {
      top: 0,
      textStyle: { color: muted },
      data: ['端到端修图', '人脸增强', '扩散类']
    },
    grid: { left: 56, right: 30, top: 46, bottom: 52 },
    xAxis: {
      name: '部署难度(越小越易)',
      nameLocation: 'middle',
      nameGap: 32,
      nameTextStyle: { color: muted },
      min: 1, max: 5.5,
      axisLine: { lineStyle: { color: rule } },
      axisLabel: { color: muted },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } }
    },
    yAxis: {
      name: '美颜效果',
      nameTextStyle: { color: muted },
      min: 2.5, max: 5.5,
      axisLine: { lineStyle: { color: rule } },
      axisLabel: { color: muted },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } }
    },
    series: ['端到端修图', '人脸增强', '扩散类'].map(function (cat) {
      return {
        name: cat,
        type: 'scatter',
        data: data.filter(function (d) { return d[4] === cat; }),
        symbolSize: function (d) { return d[2]; },
        itemStyle: {
          color: categoryColor[cat],
          opacity: 0.75,
          borderColor: bg2,
          borderWidth: 1
        },
        label: {
          show: true,
          position: 'top',
          formatter: function (p) { return p.data[3]; },
          color: ink,
          fontSize: 12,
          fontWeight: 600
        }
      };
    })
  });
  window.addEventListener('resize', function () { chart.resize(); });
})();

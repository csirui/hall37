/**
 * @ author: wenshan @ date: 2015.3.24 @ from: model js
 */

(function(WIN) {
  var rout = router('#'); // 初始化路由
  var DATA = {}; // 数据对象
  var index = 0; // 默认焦点
  // 这是一个将数据转化为字符串的过滤器
  Vue.filter('toStr', function(value) {
        return JSON.stringify(value, null, 4)
      })

})(window)

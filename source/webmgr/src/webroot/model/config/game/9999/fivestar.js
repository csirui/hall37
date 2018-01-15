/**
 * @ author: zhaol @ date: 2015.3.24 @ from: index js
 */

$(function() {
  // 加载菜单请求
  var jsonfile = 'game/9999/fivestar/0.json';
  var jsonvalue = null;

  var savedata = function(data) {
    alert('savedata: ' + JSON.stringify(mdatas)); 
    var params = {
      jsonfile : jsonfile,
      jsondata : JSON.stringify(data)
    };
  
    SS.setData(SS.url.model.set_json_file, params, function(da) {
      if (da.error) {
        alert('ERROR !! ' + JSON.stringify(da.error));
      } else {
        alert('SAVE DATA OK');
      }
    });
  };

  // 读取文件
  var params = {
    jsonfile : jsonfile
  };

  SS.getData(SS.url.model.get_json_file, params, function(da) {
    // 加载数据
    jsonvalue=da.result.datas;

    $('#editor').jsonEditor(jsonvalue, {
      change: function() {
        alert('Now data:' + JSON.stringify(jsonvalue));
     }
    });
    alert('value:' + JSON.stringify(jsonvalue));
  });
});
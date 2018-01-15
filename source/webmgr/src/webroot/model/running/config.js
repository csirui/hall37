/**
 * @ author: wenshan @ date: 2015.3.24 @ from: index js
 */

$(function() {
      var jsonfile = '._confprojects_.json';
      var jsonvue = null;
      var params = {
        jsonfile : jsonfile
      };
      SS.getData(SS.url.model.get_json_file, params, function(da) {
            // 加载数据
            if (da && da.result && da.result.datas.length > 0) {
              $('#firstpackage').show();
              var projpkgs = [];
              for (var x in da.result.datas) {
                var pkgname = da.result.datas[x];
                projpkgs.push({
                      pkgname : pkgname
                    });
              }
              jsonvue = new Vue({
                    el : '#dataContent',
                    data : {
                      projpkgs : projpkgs
                    }
                  });
            }
          });
      $('#firstpackage').hide();
    });

function doServerAction(actionName, actionParams) {
  var params = {
    'action_user' : 'zqh',
    'action_name' : actionName,
    'action_params' : JSON.stringify(actionParams)
  };
  SS.setData(SS.url.model.add_action, params, function(da) {
        if (da.error) {
          alert('ERROR !! ' + JSON.stringify(da.error));
        } else {
          var action = da.result.action;
          var auuid = action.uuid;
          window.parent.showLogViewWindow(auuid);
        }
      });
}

function checkConfig() {
  doServerAction('config_check', {});
}

function updateConfig() {
  doServerAction('config_update', {});
}

function svnUpdateAll() {
  doServerAction('svn_update_all', {});
}

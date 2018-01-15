/**
 * @ author: wenshan @ date: 2015.3.24 @ from: index js
 */

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

var curAction = null;
var curSvnUser = '';
var curSvnPwd = '';
var actcode = null;

function svnUpdateAll(button) {
  doActionSvnUpdateDialog(button, function() {
        doServerAction('svn_update_all', {
              'svnuser' : curSvnUser,
              'svnpwd' : curSvnPwd
            });
      });
}

function svnUpdateConfig(button) {
  doActionSvnUpdateDialog(button, function() {
        doServerAction('svn_update_config', {
              'svnuser' : curSvnUser,
              'svnpwd' : curSvnPwd
            });
      });
}

function compileProject(button) {
  doActionDialog(button, function() {
        doServerAction('compile_source', {});
      });
}

function checkConfig(button) {
  doActionDialog(button, function() {
        doServerAction('config_check', {});
      });
}

function stopAllProcess(button) {
  doActionDialog(button, function() {
        doServerAction('stop_all_process', {});
      });
}

function removeAllLogs(button) {
  doActionDialog(button, function() {
        doServerAction('remove_all_logs', {});
      });
}

function configCompileStart(button) {
  doActionDialog(button, function() {
        doServerAction('config_compile_start', {});
      });
}

function configUpdate(button) {
  doActionDialog(button, function() {
        doServerAction('config_update', {});
      });
}

function restartMgr(button) {
  doActionDialog(button, function() {
        doServerAction('restart_mgr_thread', {});
      });
}

function pushCode(button) {
  doActionDialog(button, function() {
        doServerAction('push_bin', {});
      });
}

function pushWeb(button) {
  doActionDialog(button, function() {
        doServerAction('push_web', {});
      });
}

function resetSelectedProcess(button) {
  var sids = [];
  for (sid in lasted_select_sids) {
    if (lasted_select_sids[sid] == 1) {
      sids.push(sid);
    }
  }
  if (sids.length == 0) {
    alert('请选择需要启动的进程！！');
    return;
  }
  doActionDialog(button, function() {
        doServerAction('reset', {
              processids : sids
            });
      });
}

function getOneCode() {
  var i = parseInt(Math.random() * 10)
  return '' + i;
}

function doActionDialog(button, funAction) {
  actcode = getOneCode() + getOneCode() + getOneCode() + getOneCode();
  var actname = $(button).text();
  $('#actcode1').text(actcode);
  $('#actname').text(actname);
  $('#actip').text(top.window.headInfo.localip);
  $('#actcode2').val(actcode);
  curAction = funAction;
  $('#actdlg').dialog('open');
}

function doActionSvnUpdateDialog(button, funAction) {
  var actname = $(button).text();
  $('#svnactname').text(actname);
  $('#svnactip').text(top.window.headInfo.localip);
  curAction = funAction;
  $('#actsvndlg').dialog('open');
}

$(function() {
      $('#actdlg').dialog({
            title : '确认操作',
            iconCls : "icon-edit",
            collapsible : false,
            minimizable : false,
            maximizable : false,
            resizable : false,
            width : 400,
            height : 220,
            modal : true,
            onClose : function() {
            },
            buttons : [{
                  text : 'Ok',
                  iconCls : 'icon-ok',
                  handler : function() {
                    if ($('#actcode2').val() == actcode) {
                      $('#actdlg').dialog('close');
                      curAction();
                    } else {
                      alert('操作确认码不正确');
                      $('#actdlg').dialog('close');
                    }
                  }
                }, {
                  text : 'Cancel',
                  iconCls : 'icon-cancel',
                  handler : function() {
                    $('#actdlg').dialog('close');
                  }
                }]
          });
      $('#actdlg').dialog('close');

      $('#actsvndlg').dialog({
            title : '确认SVN操作',
            iconCls : "icon-edit",
            collapsible : false,
            minimizable : false,
            maximizable : false,
            resizable : false,
            width : 400,
            height : 220,
            modal : true,
            onClose : function() {
            },
            buttons : [{
                  text : 'Ok',
                  iconCls : 'icon-ok',
                  handler : function() {
                    curSvnUser = $('#svnuser').val();
                    curSvnPwd = $('#svnpwd').val();
                    curAction();
                    $('#actsvndlg').dialog('close');
                  }
                }, {
                  text : 'Cancel',
                  iconCls : 'icon-cancel',
                  handler : function() {
                    $('#actsvndlg').dialog('close');
                  }
                }]
          });
      $('#actsvndlg').dialog('close');
    });

/**
 * @ author: wenshan @ date: 2015.3.24 @ from: index js
 */

var action_list = null;
var selectedActionUuid = null;
var curLogUuid = null;
var process_list = null;
var lasted_select_sids = {};

function reloadActionList() {
  SS.setData(SS.url.model.get_action_list, {}, function(da) {
        if (da.error) {
          alert('ERROR !! ' + JSON.stringify(da.error));
        } else {
          var actions = da.result.actions;
          var mlist = [];
          for (var x in actions) {
            var act = actions[x];
            var uuid = act.uuid;
            var user = act.user;
            var actname = act.action;
            var result = act.result;
            var iconCls = '';
            if (result == 'Ok') {
              iconCls = '';
            }
            mlist.push({
                  iconCls : iconCls,
                  checked : false,
                  text : actname + ' | ' + uuid,
                  attributes : {
                    uuid : uuid,
                    user : user,
                    time : act.time,
                    actname : actname
                  }
                });
          }
          $('#logfile_menu').tree({
                checkbox : true,
                onlyLeafCheck : true,
                data : mlist,
                onSelect : function(node) {
                  showActionLog(node);
                }
              });
          action_list = mlist;
          if (selectedActionUuid) {
            selectCurrentAction(selectedActionUuid);
          }
        }
      });
}

function selectCurrentAction(auuid) {
  selectedActionUuid = auuid;
  if (action_list) {
    for (var x in action_list) {
      var an = action_list[x];
      if (an.attributes.uuid == auuid) {
        doubleClickMenuNode(an.text);
        return;
      }
    }
  }
  reloadActionList();
}

function doubleClickMenuNode(text) {
  var nodes = $('#logfile_menu').tree('getRoots');
  for (var x in nodes) {
    var n = nodes[x];
    if (n.text == text) {
      $('#logfile_menu').tree('select', n.target);
      break;
    }
  }
}

function showActionLog(node) {
  var atts = node.attributes;
  if (curLogUuid == atts.uuid) {
    return;
  }
  curLogUuid = atts.uuid;
  $('#action_uuid').html(atts.uuid);
  $('#action_user').html(atts.user);
  $('#action_time').html(atts.time);
  $('#action_actname').html(atts.actname);
  $('#action_log').html('');
  getActionLogContent(curLogUuid, 0);
}

function getActionLogContent(actuuid, linenum) {
  var params = {
    action_uuid : actuuid,
    line_num : linenum
  };
  SS.setData(SS.url.model.get_action_log, params, function(da) {
        if (da.error) {
          alert('ERROR !! ' + JSON.stringify(da.error));
        } else {
          var isDone = 0;
          var lines = da.result.lines;
          var htmls = [];
          for (var x in lines) {
            var l = lines[x];
            if (l.indexOf('-------- done --------') >= 0) {
              isDone = 1;
            }
            htmls.push('<div>' + lines[x] + '</div>');
            linenum += 1;
          }
          $('#action_log').append(htmls.join(''));
          $('#action_log_div').scrollTop($('#action_log_div')[0].scrollHeight);
          if (!isDone) {
            setTimeout(function() {
                  getActionLogContent(actuuid, linenum);
                }, 1000);
          }
        }
      });
}

var isallchecked = false;
function selectAllActionLogs() {
  var nodes = $('#logfile_menu').tree('getRoots');
  for (var x in nodes) {
    var n = nodes[x];
    if (isallchecked) {
      $('#logfile_menu').tree('uncheck', n.target);
    } else {
      $('#logfile_menu').tree('check', n.target);
    }
  }
  isallchecked = !isallchecked;
}

function deleteActionLogs() {
  selectAllActionLogs();
  var chks = $('#logfile_menu').tree('getChecked');
  var uuids = [];
  for (var x in chks) {
    uuids.push(chks[x].attributes.uuid);
  }
  var params = {
    action_uuids : JSON.stringify(uuids)
  };
  $('.btn-success').hide();
  SS.setData(SS.url.model.remove_action, params, function(da) {
        document.location.reload();
      });
}

function reloadProcessList() {
  $('#process_ids').tree({
        checkbox : true,
        data : []
      });
  process_list = [];

  SS.setData(SS.url.model.get_process_list, {}, function(da) {
        if (da.error) {
          alert('ERROR !! ' + JSON.stringify(da.error));
        } else {
          var actions = da.result.datas;
          var mlist = [];
          var allids = {};
          for (var x in actions) {
            var proc = actions[x];
            proc['sid'] = proc['type'] + proc['id'];
            allids[proc['sid']] = 1;
            var ischecked = false;
            if (lasted_select_sids[proc['sid']] == 1) {
              ischecked = true;
            }
            lasted_select_sids[proc['sid']] = ischecked ? 1 : 0;
            var ag = proc['agent'] ? proc['agent'] : ' ';
            mlist.push({
                  checked : ischecked,
                  text : proc['sid'] + '  |  ' + proc['ip'],
                  attributes : proc
                });
            for (var sid in lasted_select_sids) {
              if (!(sid in allids)) {
                lasted_select_sids[sid] = undefined;
              }
            }
          }
          $('#process_ids').tree({
                checkbox : true,
                data : mlist,
                onCheck : function(node, checked) {
                  var sid = node.attributes['sid'];
                  if (checked) {
                    lasted_select_sids[sid] = 1;
                  } else {
                    lasted_select_sids[sid] = 0;
                  }
                },
                onSelect : function(node) {
                  var sid = node.attributes['sid'];
                  if (lasted_select_sids[sid] == 1) {
                    $('#process_ids').tree('uncheck', node.target);
                  } else {
                    $('#process_ids').tree('check', node.target);
                  }
                }
              });
          process_list = mlist;
        }
      });
}

function revertSelectedProcs() {
  var c1 = 0;
  var c2 = 0;
  for (sid in lasted_select_sids) {
    c1++;
    if (lasted_select_sids[sid] == 1) {
      c2++;
    }
  }
  var nodes = $('#process_ids').tree('getChildren');
  if (c1 == c2) {
    for (var n in nodes) {
      n = nodes[n];
      if (n.attributes && n.attributes['sid']) {
        $('#process_ids').tree('uncheck', n.target);
      }
    }
  } else {
    for (var n in nodes) {
      n = nodes[n];
      if (n.attributes && n.attributes['sid']) {
        $('#process_ids').tree('check', n.target);
      }
    }
  }
}

$(function() {
      reloadActionList();
      reloadProcessList();
      $('#loglefttabs').tabs({
            onSelect : function(title, index) {
              if (index == 1) {
                reloadProcessList();
              }
            }
          });
    });

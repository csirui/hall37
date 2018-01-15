/**
 * @ author: wenshan @ date: 2015.3.24 @ from: index js
 * editby wangtao date: 2016.1.13
 */

// 加载菜单请求
var jsonfile = 'game/8/room/0.json';
var jsonvue = null;
var mindex = 1;
var metaData = {};
var selected_rows = [];
var selected_cols = [];
var data = null;

function isObj(o) {
    var gettype = Object.prototype.toString;
    return gettype.call(o)=="[object Object]";
};


function reloadActionList(data) {
    SS.setData(SS.url.model.get_action_list, {},
    function(da) {
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
                    iconCls: iconCls,
                    checked: false,
                    text: actname + ' | ' + uuid,
                    attributes: {
                        uuid: uuid,
                        user: user,
                        time: act.time,
                        actname: actname
                    }
                });
            }
            $('#logfile_menu').tree({
                checkbox: true,
                onlyLeafCheck: true,
                data: mlist,
                onSelect: function(node) {
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

// -------------------------------------------------------
var convertDatas = function(mdata) {
    var mlist = [];
    for (var mkey in mdata) {
        var minfo = mdata[mkey];
        minfo['id'] = mkey;
        mlist.push(minfo);
    }
    mlist.sort(function(a, b) {
        var id1 = a['id'];
        var id2 = b['id'];
        return id1 > id2;
    });
    var datas = {
        'rooms': mlist
    };
    return datas;
};


// -------------------------------------------------------
function LoadJsonFile() {
    var params = {
        jsonfile: jsonfile
    };

    SS.getData(SS.url.model.get_json_file, params,
    function(da) {
        showRoomConfGrid(da.result.datas);
    });
};

// -------------------------------------------------------
function generate_json() {
    var params = {
        jsonfile: jsonfile
    };
    SS.getData(SS.url.model.texas_gen_json_file, params,
    function(da) {
        var htmls = [];
        if (da.result.isOk) {
            var jsonfile = da.result.jsonfile;
            var jsonfileprev = da.result.jsonfileprev;


            htmls.push("提交日志：<br />" + da.result.svn_commit_log + "<br />");
            htmls.push("成功！<br />");
            htmls.push('<iframe name="diff_room_iframe" frameborder="0"  style="width:100%;height:100%;" src='
              + '"diff/diff.html?desc=http raw file urls'
              + '&left=' + SS.host + '/texas/get/json/file?jsonfile=' + encodeURIComponent(jsonfileprev)
              + '&right='  + SS.host + '/texas/get/json/file?jsonfile=' + encodeURIComponent(jsonfile)
              + '"'
              + '>'
              + '</iframe>'
              );
        } else {
            htmls.push("失败！<br />");
            if (da.result.error) {
                errinfo = da.result.error.split('\n').join("<br />");
                htmls.push('<pre>');
                htmls.push(errinfo);
                htmls.push('</pre>');
            }
        }
        $('#center_div').html(htmls.join(""));
        // showCompair(da.result.lastdatas, da.result.datas);
        // showRoomConfGrid(da.result.datas);
    });
};

/*
 * 提交 testing
*/
function commit_testing() {
    commit("testing");
}

/*
 * 提交 release
*/
function commit_release() {
    commit("release");
}

function real_commit () {
    var params = {
        commitlog: $('#commitlog').val(),
        branch: $('#commit_btn').attr("data-branch"),
    }
    alert("commit: " + $('#commitlog').val());
    SS.setData(SS.url.model.texas_commit, params, function(da) {
        var htmls = [];
        htmls.push(da.result.output);
        $('#center_div').html(htmls.join(""));
    });
}

function commit(branch) {


    var params = {
        branch: branch,
    };
    SS.getData(SS.url.model.texas_precommit, params,
    function(da) {
        var htmls = [];
        var jsonfile = da.result.jsonfile;
        var jsonfileprev = da.result.jsonfileprev;
        var svnlog = da.result.svnlog;

        htmls.push("<span>提交日志：</span>");
        htmls.push("<br />")
        htmls.push('<textarea type="text" id="commitlog" style="width:1000px;height:200px;">{0}</textarea>'.format(svnlog));
        htmls.push('<button id="commit_btn" onclick="real_commit()">提交</button>'.format(branch));
        htmls.push('<iframe name="diff_room_iframe" frameborder="0"  style="width:100%;height:100%;" src='
          + '"diff/diff.html?desc=http raw file urls'
          + '&left=' + SS.host + '/texas/get/json/file?jsonfile=' + encodeURIComponent(jsonfileprev)
          + '&right='  + SS.host + '/texas/get/json/file?jsonfile=' + encodeURIComponent(jsonfile)
          + '"'
          + '>'
          + '</iframe>'
          );

        $('#center_div').html(htmls.join(""));
        $('#commit_btn').attr('data-branch', branch);
    });
}



// -------------------------------------------------------
function showRoomConfGrid(datas) {
  // 显示内容
  var meta = datas
  //rebuildTable("#roomTable");

  var datas = convertDatas(datas);
  jsonvue = new Vue({
      el: '#roomTable',
      data: datas,
      methods: {
          reset: function() {
              reloadPage();
          }
      }
  });

};

// -------------------------------------------------------
function check_match_start_time() {

    $('#center_div').html('<iframe name="match_time_iframe"'
        + ' frameborder="0"'
        + ' style="width:100%;height:100%;"'
        + ' src="match_time/match_time.html"></iframe>');

};

$(function() {

    // -------------------------------------------------------
    //LoadJsonFile();
    //reloadRows();
    //reloadColumns();
});

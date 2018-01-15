/**
 * Created by windaoo on 16/8/26.
 */
/**
 * @ author: wenshan @ date: 2015.3.24 @ from: index js
 * editby wangtao date: 2016.1.13
 */

// 加载菜单请求
var jsonfile = 'game/8/room/0.json';
var jsonvue = null;
var mindex = 1;
var data = null;


function generate_json() {
    var params = {
        jsonfile: jsonfile
    };
    SS.getData(SS.url.model.texas_gen_json_file, params,
        function (da) {
            var htmls = [];
            if (da.result.isOk) {
                var jsonfile = da.result.jsonfile;
                var jsonfileprev = da.result.jsonfileprev;


                htmls.push("提交日志：<br />" + da.result.svn_commit_log + "<br />");
                htmls.push("成功！<br />");
                htmls.push('<iframe name="diff_room_iframe" frameborder="0"  style="width:100%;height:100%;" src='
                    + '"diff/diff.html?desc=http raw file urls'
                    + '&left=' + SS.host + '/texas/get/json/file?jsonfile=' + encodeURIComponent(jsonfileprev)
                    + '&right=' + SS.host + '/texas/get/json/file?jsonfile=' + encodeURIComponent(jsonfile)
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

function real_commit() {
    var params = {
        commitlog: $('#commitlog').val(),
        branch: $('#commit_btn').attr("data-branch"),
    }
    alert("commit: " + $('#commitlog').val());
    SS.setData(SS.url.model.texas_commit, params, function (da) {
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
        function (da) {
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
                + '&right=' + SS.host + '/texas/get/json/file?jsonfile=' + encodeURIComponent(jsonfile)
                + '"'
                + '>'
                + '</iframe>'
            );

            $('#center_div').html(htmls.join(""));
            $('#commit_btn').attr('data-branch', branch);
        });
}
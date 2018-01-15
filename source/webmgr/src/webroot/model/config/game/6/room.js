
function RoomListener() {
}

RoomListener.prototype.onLoad = function() {
	throw new Error('Not implement');
}

function RoomManager() {
	// key=roomId, value=RoomModel
	this.roomMap = {};
	// 监听器
	this.listener = null;
	// 0; 1 正在加载中; 2 加载完成
	this.state = 0;
}

RoomManager.prototype.newRoom = function() {

}

RoomManager.prototype.load = function() {
	if (this.state === 1) {
		throw new Error('Already loading');
	}
	
	if (this.state === 2) {
		throw new Error('Already loaded');
	}
	
	this.state = 1;
	
	self = this;
	SS.getData('dizhu_list_rooms', {}, function(rooms) {
		try {
			rooms = JSON.parse(rooms);
			if (self.state !== 1) {
				console.log('State not 1');
				return;
			}
			for (var i = 0; i < rooms.length; i++) {
				roomModel = RoomModel.decode(rooms[i]);
				self.roomMap[roomModel.roomId] = roomModel;
			}
			self.state = 2;
			console.log('RoomManager.load ok rooms=', rooms);
		} cache (e) {
			console.log('RoomManager.load SS.getData', e);
		}
	});
}

function listRooms() {
	console.log('listRooms');
}


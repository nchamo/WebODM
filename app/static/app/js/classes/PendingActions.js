const CANCEL = 1,
      REMOVE = 2,
      RESTART = 3,
      RESIZE = 4,
      IMPORT = 5,
      IMPORT_IMAGES = 6;

let pendingActions = {
    [CANCEL]: {
        descr: "Canceling..."
    },
    [REMOVE]: {
        descr: "Deleting..."
    },
    [RESTART]: {
        descr: "Restarting..."
    },
    [RESIZE]: {
      descr: "Resizing images..."
    },
    [IMPORT]: {
      descr: "Importing..."
    },
    [IMPORT_IMAGES]: {
      descr: "Importing images..."
    }
};

export default {
    CANCEL: CANCEL,
    REMOVE: REMOVE,
    RESTART: RESTART,
    RESIZE: RESIZE,
    IMPORT: IMPORT,
    IMPORT_IMAGES: IMPORT_IMAGES,

    description: function(pendingAction) {
      if (pendingActions[pendingAction]) return pendingActions[pendingAction].descr;
      else return "";
    }
};


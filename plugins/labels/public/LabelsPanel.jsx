import React from 'react';
import PropTypes from 'prop-types';
import L from 'leaflet';
import './LabelsPanel.scss';
import ErrorMessage from 'webodm/components/ErrorMessage';

export default class LabelsPanel extends React.Component {
  static defaultProps = {
  };
  static propTypes = {
    onClose: PropTypes.func.isRequired,
    tasks: PropTypes.array.isRequired,
    isShowed: PropTypes.bool.isRequired,
    map: PropTypes.object.isRequired,
    layersControl: PropTypes.object.isRequired,
  }

  constructor(props){
    super(props);

    this.state = {
        error: "",
        permanentError: "",
        loading: true,
        task: props.tasks[0] || null,
        generateLoading: false,
        addVerifiedLoading: false,
        uploadElevationMapLoading: false,
        previewLayer: null,
    };
  }

  componentDidUpdate(){
    if (this.props.isShowed && this.state.loading){
      const {id, project} = this.state.task;

      this.loadingReq = $.getJSON(`/api/projects/${project}/tasks/${id}/`)
          .done(res => {
              const { available_assets } = res;

              if (available_assets.indexOf("orthophoto.tif") === -1)
                this.setState({permanentError: "No Orthophoto is available. You need to have one to be able to label it."});
          })
          .fail(() => {
            this.setState({permanentError: `Cannot retrieve information for task ${id}. Are you are connected to the internet?`})
          })
          .always(() => {
            this.setState({loading: false});
            this.loadingReq = null;
          });
    }
  }

  componentWillUnmount(){
    if (this.loadingReq){
      this.loadingReq.abort();
      this.loadingReq = null;
    }
    if (this.generateReq){
      this.generateReq.abort();
      this.generateReq = null;
    }
  }

  waitForCompletion = (taskId, celery_task_id, cb) => {
    let errorCount = 0;

    const check = () => {
      $.ajax({
          type: 'GET',
          url: `/api/plugins/labels/task/${taskId}/labels/check/${celery_task_id}`
      }).done(result => {
          if (result.error || result.ready){
            cb(result);
          }else{
            // Retry
            setTimeout(() => check(), 2000);
          }
      }).fail(error => {
          console.warn(error);
          if (errorCount++ < 10) setTimeout(() => check(), 2000);
          else cb(JSON.stringify(error));
      });
    };

    check();
  }

  // This function calculates the color of the polygon based on its name. 
  // This is the same logic used in LabelMe
  hashObjectColor = (name) => {
    // List of possible object colors:
    const objectColors = Array("#009900","#00ff00","#ccff00","#ffff00","#ffcc00","#ff9999","#cc0033","#ff33cc","#9933ff","#990099","#000099","#006699","#00ccff","#999900");
    
    // Pseudo-randomized case insensitive hashing based on object name:
    let hash = 0;
    name = name.toUpperCase(); 
    for (let i = 0; i < name.length;i++) {
      const tmp = name.substring(i,i+1);
      for(let j = 1; j <= 255; j++) {
        if (unescape('%'+j.toString(16)) == tmp) {
          hash += j;
          break;
        }
      }
    }
    hash = (((hash + 567) * 1048797) % objectColors.length);
    
    return objectColors[hash];
  }

  addVerified = () => {
    const { map, layersControl } = this.props;
    const taskId = this.state.task.id;
    
    this.generateAndDoWhenReady('addVerifiedLoading', 'generateverified', null, (celery_task_id, result) => {
      const url = `/api/plugins/labels/task/${taskId}/labels/downloadverified/${celery_task_id}`;
      $.getJSON(url)
        .done((geojson) => {
          if (geojson.error) {
              this.setState({addVerifiedLoading: false, 'error': JSON.stringify(geojson.error)});
          } else {
            try{
              this.removePreview();
              if (geojson.features.length == 0) {
                throw 'Failed to find verified labels. Don\'t forget to verify them before loading them.'
              }

              this.setState({previewLayer: L.geoJSON(geojson, {
                onEachFeature: (feature, layer) => {
                    layer.bindPopup(`<b>Name:</b> ${feature.properties.name}<BR><b>Attributes:</b> ${feature.properties.attributes}`);
                },
                style: feature => {
                    const color = this.hashObjectColor(feature.properties.name);
                    return { color: color, fillColor: color, fillOpacity: 0.3 };
                }
              })});
              this.state.previewLayer.setOpacity = (opacity) => {
                this.state.previewLayer.setStyle({ opacity: opacity, fillOpacity: opacity * 0.3 });
              }
              this.state.previewLayer.addTo(map);
              layersControl.addOverlay(this.state.previewLayer, "Verified Labels");
              this.setState({addVerifiedLoading: false});
            } catch(e) {
              this.setState({addVerifiedLoading: false, 'error': e});
            }
           }
         })
       .fail(error => this.setState({addVerifiedLoading: false, 'error': JSON.stringify(error)}));
    });  
  }
  
  uploadElevationMap = () => {
    const { map, layersControl } = this.props;
    const result = Object.values(layersControl._layers)
        .filter(layer => layer.overlay)
        .filter(layer => layer.name === "Elevation Map")
        .map(layer => layer.layer)
        .filter(layer => layer.geojson)
        .map(layer => layer.geojson);
    
    if (result.length === 0) {
       this.setState({error: 'You must generate an elevation map in order to execute this action.'});
    } else {
      const geojson = result[0];
      this.generateAndDoWhenReady('uploadElevationMapLoading', 'upload', { geojson : JSON.stringify(geojson) }, () => {});
    }      
  }

  generatePngFromTiff = () => {
    this.generateAndDoWhenReady('generateLoading', 'generatepng', null, (celery_task_id, result) => {
      const url = `${window.location.protocol}//${window.location.host}/labelme?folder=${result.folder}&file=${result.file}`;
      window.open(url,'_blank');
    })
  }
  
  removePreview = () => {
    const { map, layersControl } = this.props;
    if (this.state.previewLayer){
      map.removeLayer(this.state.previewLayer);
      layersControl.removeLayer(this.state.previewLayer);
      this.setState({previewLayer: null});
    }
  }
  
  generateAndDoWhenReady = (loadingProp, action, data, success) => {
    this.setState({[loadingProp]: true, error: ""});
    const taskId = this.state.task.id;
    this.generateReq = $.ajax({
        type: 'POST',
        url: `/api/plugins/labels/task/${taskId}/labels/${action}`,
        data: data,
    }).done(result => {
        if (result.celery_task_id){
          this.waitForCompletion(taskId, result.celery_task_id, newResult => {
            if (newResult.error) {
              this.setState({[loadingProp]: false, error: newResult.error});
            } else {
              this.setState({[loadingProp]: false});
              success(result.celery_task_id, newResult);
            }
          });
        } else if (result.error) {
            this.setState({[loadingProp]: false, error: result.error});
        } else {
            this.setState({[loadingProp]: false, error: "Invalid response: " + result});
        }
    }).fail(error => {
        this.setState({[loadingProp]: false, error: JSON.stringify(error)});
    });
  }

  render(){
    const { loading, task, error, permanentError, addVerifiedLoading,
            generateLoading, uploadElevationMapLoading, previewLayer } = this.state;
    let content = "";
    if (loading) content = (<span><i className="fa fa-circle-o-notch fa-spin"></i> Loading...</span>);
    else if (permanentError) content = (<div className="alert alert-warning">{permanentError}</div>);
    else{
      content = (<div>
        <ErrorMessage bind={[this, "error"]} />
        <div className="row action-buttons">
          <div className="text-right">
            <button onClick={this.generatePngFromTiff}
                    disabled={generateLoading || uploadElevationMapLoading} type="button" className="btn btn-sm btn-primary btn-preview">
              {generateLoading ? <i className="fa fa-spin fa-circle-o-notch"/> : <i className="glyphicon glyphicon-pencil"/>} Start Labeling
            </button>
            <br/>
            <div className="col-sm-3"></div>
            <button onClick={this.addVerified}
                    disabled={addVerifiedLoading} type="button" className="btn btn-sm btn-primary btn-preview">
              {addVerifiedLoading ? <i className="fa fa-spin fa-circle-o-notch"/> : <i className="glyphicon glyphicon-cloud-download"/>} Load Verified Labels
            </button>
            <br/>
            <div className="col-sm-3"></div>
            <button onClick={this.uploadElevationMap}
                    disabled={uploadElevationMapLoading} type="button" className="btn btn-sm btn-primary btn-preview">
              {uploadElevationMapLoading ? <i className="fa fa-spin fa-circle-o-notch"/> : <i className="glyphicon glyphicon-cloud-upload"/>} Upload Elevation Map
            </button>
          </div>
        </div>
      </div>);
    }

    return (<div className="labels-panel">
      <span className="close-button" onClick={this.props.onClose}/>
      <div className="title">Labels</div>
      <hr/>
      {content}
    </div>);
  }
}
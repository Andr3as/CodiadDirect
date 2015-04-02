<?php
/*
 * Copyright (c) Codiad & Andr3as, distributed
 * as-is and without warranty under the MIT License. 
 * See http://opensource.org/licenses/MIT for more information.
 * This information must remain intact.
 */
    error_reporting(0);

    require_once('../../common.php');
    checkSession();
    
    switch($_GET['action']) {
        
        case 'getUserProjects':
            $projects_assigned = false;
            if(file_exists(BASE_PATH . "/data/" . $_SESSION['user'] . '_acl.php')){
                $projects_assigned = getJSON($_SESSION['user'] . '_acl.php');
            }
            $projects = getJSON('projects.php');
            sort($projects);
            $user_projects = array();
            foreach($projects as $project=>$data){
                if($projects_assigned && !in_array($data['path'],$projects_assigned)){ 
                	continue;
                }
                array_push($user_projects,$data);
            }
            echo json_encode(array("status" => "success", "projects" => $user_projects));
            break;
            
        case 'saveFile':
        	if (isset($_GET['path']) && $_POST['content']) {
        		$result = file_put_contents(getWorkspacePath($_GET['path']),$_POST['content']);
        		if ($result === false) {
        			echo '{"status":"error","message":"Failed to save file"}';
        		} else {
        			echo '{"status":"error","message":"File saved"}';
        		}
        	} else {
        		echo '{"status":"error","message":"Missing Parameter"}';
        	}
        	break;
        
        default:
            echo '{"status":"error","message":"No Type"}';
            break;
    }
    
    
    function getWorkspacePath($path) {
		//Security check
		if (!Common::checkPath($path)) {
			die('{"status":"error","message":"Invalid path"}');
		}
        if (strpos($path, "/") === 0) {
            //Unix absolute path
            return $path;
        }
        if (strpos($path, ":/") !== false) {
            //Windows absolute path
            return $path;
        }
        if (strpos($path, ":\\") !== false) {
            //Windows absolute path
            return $path;
        }
        return WORKSPACE . "/" . $path;
    }
?>